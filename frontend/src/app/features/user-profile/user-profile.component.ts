import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/auth/auth.service';
import { TimeAgoPipe } from '../../shared/pipes/time-ago.pipe';
import type { User } from '../../core/models/index';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [TimeAgoPipe, FormsModule],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.scss',
})
export class UserProfileComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  auth = inject(AuthService);

  user = signal<User | null>(null);
  loading = signal(true);

  // Edit name state
  editingName = signal(false);
  editNameValue = signal('');
  savingName = signal(false);

  // Avatar upload state
  avatarUploading = signal(false);
  avatarPreview = signal<string | null>(null);

  isOwnProfile = computed(() => {
    const u = this.user();
    const cu = this.auth.currentUser();
    return !!(u && cu && u.id === cu.id);
  });

  ngOnInit() {
    const username = this.route.snapshot.paramMap.get('username') ?? '';
    this.api.get<User>(`/u/${username}`).subscribe({
      next: (u) => { this.user.set(u); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  // ── Name editing ──────────────────────────────────────────────────────────

  startEditName() {
    this.editNameValue.set(this.user()?.name ?? '');
    this.editingName.set(true);
  }

  cancelEditName() {
    this.editingName.set(false);
  }

  saveName() {
    const u = this.user();
    if (!u) return;
    this.savingName.set(true);
    this.api.put<User>(`/u/${u.username}`, { name: this.editNameValue() }).subscribe({
      next: (updated) => {
        this.user.set(updated);
        this.editingName.set(false);
        this.savingName.set(false);
        if (this.isOwnProfile()) {
          this.auth.currentUser.set(updated);
        }
      },
      error: () => {
        alert('No se pudo guardar el nombre.');
        this.savingName.set(false);
      },
    });
  }

  // ── Avatar upload ─────────────────────────────────────────────────────────

  triggerAvatarInput() {
    const input = document.getElementById('avatar-file-input') as HTMLInputElement;
    input?.click();
  }

  onAvatarFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    // Show local preview immediately
    const reader = new FileReader();
    reader.onload = (e) => this.avatarPreview.set(e.target?.result as string);
    reader.readAsDataURL(file);

    this.uploadAvatar(file);
    // Reset so the same file can be re-selected
    input.value = '';
  }

  private uploadAvatar(file: File) {
    const u = this.user();
    if (!u) return;

    this.avatarUploading.set(true);
    const formData = new FormData();
    formData.append('file', file);

    this.api.postForm<User>(`/u/${u.username}/avatar`, formData).subscribe({
      next: (updated) => {
        this.user.set(updated);
        this.avatarPreview.set(null); // Use server URL
        this.avatarUploading.set(false);
        if (this.isOwnProfile()) {
          this.auth.currentUser.set(updated);
        }
      },
      error: () => {
        alert('No se pudo subir la imagen. Verifica que sea JPEG, PNG, GIF o WebP y pese menos de 5 MB.');
        this.avatarUploading.set(false);
        this.avatarPreview.set(null);
      },
    });
  }
}

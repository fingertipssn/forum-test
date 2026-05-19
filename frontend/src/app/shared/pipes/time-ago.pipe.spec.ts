import { TimeAgoPipe } from './time-ago.pipe';

describe('TimeAgoPipe', () => {
  let pipe: TimeAgoPipe;

  beforeEach(() => {
    pipe = new TimeAgoPipe();
  });

  it('should create', () => {
    expect(pipe).toBeTruthy();
  });

  it('should return empty string for null', () => {
    expect(pipe.transform(null)).toBe('');
  });

  it('should return empty string for undefined', () => {
    expect(pipe.transform(undefined)).toBe('');
  });

  it('should return empty string for empty string', () => {
    expect(pipe.transform('')).toBe('');
  });

  it('should return "hace un momento" for < 60 seconds ago', () => {
    const recent = new Date(Date.now() - 30 * 1000);
    expect(pipe.transform(recent)).toBe('hace un momento');
  });

  it('should return minutes for < 1 hour ago', () => {
    const twoMinsAgo = new Date(Date.now() - 2 * 60 * 1000);
    const result = pipe.transform(twoMinsAgo);
    expect(result).toMatch(/^hace \d+m$/);
    expect(result).toBe('hace 2m');
  });

  it('should return hours for < 24 hours ago', () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 3600 * 1000);
    const result = pipe.transform(threeHoursAgo);
    expect(result).toBe('hace 3h');
  });

  it('should return days for < 30 days ago', () => {
    const fiveDaysAgo = new Date(Date.now() - 5 * 86400 * 1000);
    const result = pipe.transform(fiveDaysAgo);
    expect(result).toBe('hace 5d');
  });

  it('should return month (singular) for 1 month ago', () => {
    const oneMonthAgo = new Date(Date.now() - 30 * 86400 * 1000);
    const result = pipe.transform(oneMonthAgo);
    expect(result).toBe('hace 1 mes');
  });

  it('should return months (plural) for 2+ months ago', () => {
    const twoMonthsAgo = new Date(Date.now() - 61 * 86400 * 1000);
    const result = pipe.transform(twoMonthsAgo);
    expect(result).toMatch(/meses/);
  });

  it('should return year (singular) for exactly 1 year ago', () => {
    const oneYearAgo = new Date(Date.now() - 366 * 86400 * 1000);
    const result = pipe.transform(oneYearAgo);
    expect(result).toMatch(/año/);
  });

  it('should return years (plural) for 2+ years ago', () => {
    const twoYearsAgo = new Date(Date.now() - 2 * 366 * 86400 * 1000);
    const result = pipe.transform(twoYearsAgo);
    expect(result).toMatch(/años/);
  });

  it('should accept a string date', () => {
    const dateStr = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    const result = pipe.transform(dateStr);
    expect(result).toMatch(/^hace \d+m$/);
  });

  it('should accept a Date object', () => {
    const date = new Date(Date.now() - 90 * 60 * 1000);
    const result = pipe.transform(date);
    expect(result).toMatch(/^hace \d+h$/);
  });
});

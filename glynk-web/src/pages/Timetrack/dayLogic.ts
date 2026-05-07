// 4am 业务日切分：凌晨 4 点之前算前一天

export const getLogicalDate = (d: Date) => {
  const logical = new Date(d);
  if (logical.getHours() < 4) {
    logical.setDate(logical.getDate() - 1);
  }
  return logical;
};

export const startOfDay = (d: Date) => {
  const logical = getLogicalDate(d);
  return new Date(logical.getFullYear(), logical.getMonth(), logical.getDate(), 4, 0, 0, 0);
};

export const endOfDay = (d: Date) => {
  const logical = getLogicalDate(d);
  return new Date(logical.getFullYear(), logical.getMonth(), logical.getDate() + 1, 3, 59, 59, 999);
};

export const startOfWeek = (d: Date) => {
  const logical = getLogicalDate(d);
  const day = logical.getDay();
  const diff = logical.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(logical.getFullYear(), logical.getMonth(), diff, 4, 0, 0, 0);
};

export const endOfWeek = (d: Date) => {
  const start = startOfWeek(d);
  return new Date(start.getFullYear(), start.getMonth(), start.getDate() + 7, 3, 59, 59, 999);
};

export const startOfMonth = (d: Date) => {
  const logical = getLogicalDate(d);
  return new Date(logical.getFullYear(), logical.getMonth(), 1, 4, 0, 0, 0);
};

export const endOfMonth = (d: Date) => {
  const logical = getLogicalDate(d);
  return new Date(logical.getFullYear(), logical.getMonth() + 1, 1, 3, 59, 59, 999);
};

// 导航：addDays/addWeeks 保留时分（一日一周步进里 logical day 也跟着步进），
// addMonths 因 logical day 的月份可能与时间戳的月份不同，必须按 logical 推。
export const addDays = (d: Date, n: number) =>
  new Date(d.getFullYear(), d.getMonth(), d.getDate() + n, d.getHours(), d.getMinutes());
export const addWeeks = (d: Date, n: number) => addDays(d, n * 7);
export const addMonths = (d: Date, n: number) => {
  const logical = getLogicalDate(d);
  return new Date(logical.getFullYear(), logical.getMonth() + n, 1, 12, 0, 0, 0);
};

import "@testing-library/jest-dom";

global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ runs: [] }),
});

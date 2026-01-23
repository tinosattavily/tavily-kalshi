import "@testing-library/jest-dom";

global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ runs: [] }),
});

jest.mock("../components/layout/HistorySidebar", () => ({
  __esModule: true,
  default: () => null,
}));


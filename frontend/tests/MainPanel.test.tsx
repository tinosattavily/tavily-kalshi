/** @jest-environment jsdom */
import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MainPanel from "../components/analysis/MainPanel";

describe("MainPanel", () => {
  test("renders thesis tab body by default", () => {
    render(
      <MainPanel
        newsTab={<div>news-body</div>}
        summaryTab={<div>summary-body</div>}
        thesisTab={<div>thesis-body</div>}
      />
    );

    expect(screen.getByText("thesis-body")).toBeInTheDocument();
    expect(screen.queryByText("news-body")).not.toBeInTheDocument();
    expect(screen.queryByText("summary-body")).not.toBeInTheDocument();
  });

  test("switches to News tab on click", async () => {
    const user = userEvent.setup();
    render(
      <MainPanel
        newsTab={<div>news-body</div>}
        summaryTab={<div>summary-body</div>}
        thesisTab={<div>thesis-body</div>}
      />
    );

    await user.click(screen.getByRole("button", { name: /news/i }));

    expect(screen.getByText("news-body")).toBeInTheDocument();
    expect(screen.queryByText("thesis-body")).not.toBeInTheDocument();
  });

  test("switches to Summary tab on click", async () => {
    const user = userEvent.setup();
    render(
      <MainPanel
        newsTab={<div>news-body</div>}
        summaryTab={<div>summary-body</div>}
        thesisTab={<div>thesis-body</div>}
      />
    );

    await user.click(screen.getByRole("button", { name: /summary/i }));

    expect(screen.getByText("summary-body")).toBeInTheDocument();
    expect(screen.queryByText("thesis-body")).not.toBeInTheDocument();
  });

  test("displays news count badge when newsCount is provided", () => {
    render(
      <MainPanel
        newsCount={7}
        newsTab={<div>news-body</div>}
        summaryTab={<div>summary-body</div>}
        thesisTab={<div>thesis-body</div>}
      />
    );

    expect(screen.getByText("7")).toBeInTheDocument();
  });
});

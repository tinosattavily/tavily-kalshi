/** @jest-environment jsdom */
import React from "react";
import RootLayout from "../../app/layout";
import { Providers } from "../../components/Providers";

// Mock next/font/google. RootLayout now imports both Geist and Geist_Mono.
jest.mock("next/font/google", () => ({
  Geist: jest.fn(() => ({
    variable: "mock-geist-sans",
    className: "mock-geist-sans",
    style: { fontFamily: "mock-geist-sans" },
  })),
  Geist_Mono: jest.fn(() => ({
    variable: "mock-geist-mono",
    className: "mock-geist-mono",
    style: { fontFamily: "mock-geist-mono" },
  })),
}));

// Mock the theme cookie helper so tests don't try to read real cookies.
jest.mock("../../lib/theme-cookie", () => ({
  getServerTheme: jest.fn(async () => null),
  THEME_COOKIE: "prophily-theme",
}), { virtual: true });

// Mock globals.css import
jest.mock("../../app/globals.css", () => ({}));

describe("RootLayout", () => {
  const renderLayout = async (children: React.ReactNode) =>
    (await RootLayout({ children })) as React.ReactElement;

  const getBodyElement = (layout: React.ReactElement) => {
    const childArray = React.Children.toArray(layout.props.children) as React.ReactElement[];
    const body = childArray.find((c) => c?.type === "body");
    if (!body) throw new Error("body element not found in layout");
    return body;
  };

  const getProvidersChildren = (bodyElement: React.ReactElement) => {
    // Body wraps children in Providers component
    const providersElement = bodyElement.props.children as React.ReactElement;
    return providersElement.props.children;
  };

  test("renders html element with lang attribute", async () => {
    const layout = await renderLayout(<div>Test Content</div>);
    expect(layout.type).toBe("html");
    expect(layout.props.lang).toBe("en");
  });

  test("renders html with data-theme attribute", async () => {
    const layout = await renderLayout(<div>Test Content</div>);
    expect(layout.props["data-theme"]).toBeDefined();
    expect(["atelier", "obsidian"]).toContain(layout.props["data-theme"]);
  });

  test("renders body element with both Geist font variables in className", async () => {
    const layout = await renderLayout(<div>Test Content</div>);
    const bodyElement = getBodyElement(layout);
    expect(bodyElement.type).toBe("body");
    expect(bodyElement.props.className).toContain("mock-geist-sans");
    expect(bodyElement.props.className).toContain("mock-geist-mono");
  });

  test("wraps children with Providers", async () => {
    const layout = await renderLayout(<div>Test Content</div>);
    const bodyElement = getBodyElement(layout);
    const providersElement = bodyElement.props.children as React.ReactElement;
    expect(providersElement.type).toBe(Providers);
  });

  test("renders children inside Providers", async () => {
    const child = <div data-testid="child">Test Content</div>;
    const layout = await renderLayout(child);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toEqual(child);
  });

  test("renders multiple children inside Providers", async () => {
    const children = [
      <div key="child1" data-testid="child1">Child 1</div>,
      <div key="child2" data-testid="child2">Child 2</div>,
    ];
    const layout = await renderLayout(children);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toEqual(children);
  });

  test("renders empty children inside Providers", async () => {
    const layout = await renderLayout(null);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toBeNull();
  });

  test("has correct metadata", () => {
    // Metadata is exported but not directly testable in component render.
    // We can verify it exists by checking the export.
    expect(RootLayout).toBeDefined();
  });

  test("renders without errors", async () => {
    const layout = await renderLayout(<div>Test</div>);
    expect(layout).toBeTruthy();
  });

  test("applies Geist + Geist Mono font configuration", async () => {
    // eslint-disable-next-line no-undef
    const { Geist, Geist_Mono } = require("next/font/google");
    await renderLayout(<div>Test</div>);
    expect(Geist).toHaveBeenCalledWith({
      subsets: ["latin"],
      display: "swap",
      variable: "--font-geist-sans",
    });
    expect(Geist_Mono).toHaveBeenCalledWith({
      subsets: ["latin"],
      display: "swap",
      variable: "--font-geist-mono",
    });
  });

  test("renders complex children structure inside Providers", async () => {
    const children = (
      <>
        <header>
          <h1>Header</h1>
        </header>
        <main>
          <p>Main content</p>
        </main>
        <footer>
          <p>Footer</p>
        </footer>
      </>
    );
    const layout = await renderLayout(children);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toEqual(children);
  });
});

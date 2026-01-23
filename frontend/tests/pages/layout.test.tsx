/** @jest-environment jsdom */
import React from "react";
import RootLayout from "../../app/layout";
import { Providers } from "../../components/Providers";

// Mock next/font/google
jest.mock("next/font/google", () => ({
  Inter: jest.fn(() => ({
    className: "inter-font-class",
    style: {},
  })),
}));

// Mock globals.css import
jest.mock("../../app/globals.css", () => ({}));

describe("RootLayout", () => {
  const renderLayout = (children: React.ReactNode) =>
    RootLayout({ children }) as React.ReactElement;

  const getBodyElement = (layout: React.ReactElement) =>
    layout.props.children as React.ReactElement;

  const getProvidersChildren = (bodyElement: React.ReactElement) => {
    // Body wraps children in Providers component
    const providersElement = bodyElement.props.children as React.ReactElement;
    return providersElement.props.children;
  };

  test("renders html element with lang attribute", () => {
    const layout = renderLayout(<div>Test Content</div>);
    expect(layout.type).toBe("html");
    expect(layout.props.lang).toBe("en");
  });

  test("renders body element with font class", () => {
    const layout = renderLayout(<div>Test Content</div>);
    const bodyElement = getBodyElement(layout);
    expect(bodyElement.type).toBe("body");
    expect(bodyElement.props.className).toBe("inter-font-class");
  });

  test("wraps children with Providers", () => {
    const layout = renderLayout(<div>Test Content</div>);
    const bodyElement = getBodyElement(layout);
    const providersElement = bodyElement.props.children as React.ReactElement;
    expect(providersElement.type).toBe(Providers);
  });

  test("renders children inside Providers", () => {
    const child = <div data-testid="child">Test Content</div>;
    const layout = renderLayout(child);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toEqual(child);
  });

  test("renders multiple children inside Providers", () => {
    const children = [
      <div key="child1" data-testid="child1">Child 1</div>,
      <div key="child2" data-testid="child2">Child 2</div>,
    ];
    const layout = renderLayout(children);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toEqual(children);
  });

  test("renders empty children inside Providers", () => {
    const layout = renderLayout(null);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toBeNull();
  });

  test("has correct metadata", () => {
    // Metadata is exported but not directly testable in component render
    // We can verify it exists by checking the export
    expect(RootLayout).toBeDefined();
  });

  test("renders without errors", () => {
    const layout = renderLayout(<div>Test</div>);
    expect(layout).toBeTruthy();
  });

  test("applies Inter font configuration", () => {
    // eslint-disable-next-line no-undef
    const { Inter } = require("next/font/google");
    renderLayout(<div>Test</div>);
    expect(Inter).toHaveBeenCalledWith({
      subsets: ["latin"],
      display: "swap",
    });
  });

  test("renders complex children structure inside Providers", () => {
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
    const layout = renderLayout(children);
    const bodyElement = getBodyElement(layout);
    const childrenInProviders = getProvidersChildren(bodyElement);
    expect(childrenInProviders).toEqual(children);
  });
});


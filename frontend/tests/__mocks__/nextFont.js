/* eslint-disable no-undef */
// Mock for next/font/google.
// Each font factory returns an object with the same shape next/font produces
// in real builds — `.variable`, `.className`, and `.style.fontFamily` —
// so components that read any of those during render continue to work.

function makeFontMock(varName) {
  return function () {
    return {
      variable: `--mock-${varName}`,
      className: `mock-${varName}`,
      style: { fontFamily: `mock-${varName}` },
    };
  };
}

module.exports = {
  Courier_Prime: makeFontMock("courier"),
  Geist: makeFontMock("geist-sans"),
  Geist_Mono: makeFontMock("geist-mono"),
  Inter: makeFontMock("inter"),
};

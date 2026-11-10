/* Copyright (c) 2026 Alex Voss
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT license. See LICENSE in the project root.
 */

window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};

document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});

component$.subscribe(({ ref }) => {
  if (ref.classList.contains("md-annotation")) MathJax.typesetPromise([ref]);
});

require.config({ paths: { vs: "./node_modules/monaco-editor/min/vs" } });

require(["vs/editor/editor.main"], function () {

  // -----------------------------
  // 1️⃣ Register language
  // -----------------------------
  monaco.languages.register({ id: "bookmark" });

  // -----------------------------
  // 2️⃣ Syntax highlighting
  // -----------------------------
  monaco.languages.setMonarchTokensProvider("bookmark", {
    tokenizer: {
      root: [
        // Commands starting with ;
        [/;[a-zA-Z_][\w]*/, "command"],

        // Numbers
        [/\d+/, "number"],

        // Strings in quotes
        [/".*?"/, "string"],

        // Operators and punctuation
        [/[\(\)=,:\-]/, "operator"],

        // Bullet points
        [/^\s*-\s.*$/, "bullet"],

        // Whitespace
        [/\s+/, "white"]
      ]
    }
  });

  // -----------------------------
  // 3️⃣ Theme
  // -----------------------------
  monaco.editor.defineTheme("bkm-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "command", foreground: "FF9900", fontStyle: "bold" },
      { token: "string", foreground: "00FF00" },
      { token: "number", foreground: "FF00FF" },
      { token: "operator", foreground: "00FFFF" },
      { token: "bullet", foreground: "AAAAAA" }
    ],
    colors: {
      "editor.background": "#1e1e1e",
      "editorCursor.foreground": "#FFFFFF"
    }
  });

  // -----------------------------
  // 4️⃣ Create editor
  // -----------------------------
  const editor = monaco.editor.create(document.getElementById("editor"), {
    value: `;document()
;setmargin(all=50)
;initfont(name="CMU", path="~/Library/Fonts/cmunrm.ttf")
;setfont(name="CMU", size=14)
;heading(): 8th - 21st
;paragraph():
  - Pull-ups            - 4 sets, rest 90s
  - Static holds        - 2 sets, hold 10s`,
    language: "bookmark",
    theme: "bkm-dark",
    automaticLayout: true
  });
  monaco.languages.registerCompletionItemProvider("bookmark", {
    triggerCharacters: [";"],

    provideCompletionItems: (model, position) => {
      const lineContent = model.getLineContent(position.lineNumber);
      const prefix = lineContent.slice(0, position.column - 1); // content before cursor

      // Match the last command starting with a semicolon
      const match = prefix.match(/;[a-zA-Z_]*$/);

      if (!match) return { suggestions: [] }; // <-- no semicolon? return empty
      const startColumn = match ? prefix.length - match[0].length + 1 : position.column;

      const suggestions = [
        { label: ";document", kind: monaco.languages.CompletionItemKind.Function, insertText: ";document()", documentation: "Start a new document" },
        { label: ";setmargin", kind: monaco.languages.CompletionItemKind.Function, insertText: ";setmargin(all=0)", documentation: "Set margins" },
        { label: ";initfont", kind: monaco.languages.CompletionItemKind.Function, insertText: ';initfont(name="CMU", path="~/Library/Fonts/cmunrm.ttf")', documentation: "Initialize font" },
        { label: ";setfont", kind: monaco.languages.CompletionItemKind.Function, insertText: ';setfont(name="CMU", size=14)', documentation: "Set font and size" },
        { label: ";heading", kind: monaco.languages.CompletionItemKind.Function, insertText: ";heading(): ", documentation: "Add a heading" },
        { label: ";paragraph", kind: monaco.languages.CompletionItemKind.Function, insertText: ";paragraph():\n  - ", documentation: "Start a paragraph with bullets" }
      ];

      // Set the correct replacement range
      suggestions.forEach(s => {
        s.range = {
          startLineNumber: position.lineNumber,
          startColumn: startColumn,
          endLineNumber: position.lineNumber,
          endColumn: position.column
        };
      });

      return { suggestions };
    }
  });

  // -----------------------------
  // 6️⃣ Optional: manual trigger (Ctrl+Space)
  // -----------------------------
  // editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Space, () => {
  //   editor.trigger("keyboard", "editor.action.triggerSuggest", {});
  // });

});

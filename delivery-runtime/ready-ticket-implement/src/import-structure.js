const IDENTIFIER_START = /[A-Za-z_$]/;
const IDENTIFIER_PART = /[A-Za-z0-9_$]/;

const REGEX_PREFIX_KEYWORDS = new Set([
  "await", "case", "delete", "do", "else", "in", "instanceof", "new", "of", "return", "throw", "typeof", "void", "yield",
]);
const REGEX_PREFIX_PUNCTUATION = new Set([
  "(", "[", "{", "=", ",", ":", ";", "!", "?", "&", "|", "+", "-", "*", "%", "^", "~", "<", ">", "=>",
]);

function canStartRegex(tokens) {
  let previous = null;
  for (let index = tokens.length - 1; index >= 0; index -= 1) {
    if (!["comment", "template"].includes(tokens[index].type)) {
      previous = tokens[index];
      break;
    }
  }
  if (!previous) return true;
  return (previous.type === "identifier" && REGEX_PREFIX_KEYWORDS.has(previous.value))
    || (previous.type === "punctuation" && REGEX_PREFIX_PUNCTUATION.has(previous.value));
}

export function tokenizeJavaScript(text) {
  const tokens = [];
  const errors = [];
  const templateExpressions = [];
  let index = 0;
  let line = 1;
  let braceDepth = 0;

  const emit = (type, value, start, startLine) => {
    tokens.push({ type, value, start, end: index, line: startLine });
  };
  const advance = () => {
    if (text[index] === "\n") line += 1;
    index += 1;
  };
  const error = (message, start, startLine) => {
    errors.push({ message, offset: start, line: startLine });
  };

  const scanTemplateText = (hasOpeningBacktick = true) => {
    const start = index;
    const startLine = line;
    if (hasOpeningBacktick) advance();
    let segment = "";
    while (index < text.length) {
      const character = text[index];
      if (character === "\\") {
        segment += character;
        advance();
        if (index < text.length) {
          segment += text[index];
          advance();
        }
        continue;
      }
      if (character === "`") {
        advance();
        emit("template", segment, start, startLine);
        return;
      }
      if (character === "$" && text[index + 1] === "{") {
        advance();
        advance();
        emit("template", segment, start, startLine);
        tokens.push({ type: "punctuation", value: "${", start: index - 2, end: index, line });
        templateExpressions.push(braceDepth);
        braceDepth += 1;
        return;
      }
      segment += character;
      advance();
    }
    emit("template", segment, start, startLine);
    error("unterminated template literal", start, startLine);
  };

  while (index < text.length) {
    const character = text[index];
    if (/\s/.test(character)) {
      advance();
      continue;
    }

    if (character === "/" && text[index + 1] === "/") {
      const start = index;
      const startLine = line;
      while (index < text.length && text[index] !== "\n") advance();
      emit("comment", text.slice(start, index), start, startLine);
      continue;
    }
    if (character === "/" && text[index + 1] === "*") {
      const start = index;
      const startLine = line;
      advance();
      advance();
      while (index < text.length && !(text[index] === "*" && text[index + 1] === "/")) advance();
      if (index >= text.length) {
        emit("comment", text.slice(start, index), start, startLine);
        error("unterminated block comment", start, startLine);
        continue;
      }
      advance();
      advance();
      emit("comment", text.slice(start, index), start, startLine);
      continue;
    }

    if (character === "'" || character === "\"") {
      const quote = character;
      const start = index;
      const startLine = line;
      let value = "";
      advance();
      let terminated = false;
      while (index < text.length) {
        if (text[index] === "\\") {
          advance();
          if (index >= text.length) break;
          if (text[index] === "\n" || text[index] === "\r") {
            if (text[index] === "\r") advance();
            if (text[index] === "\n") advance();
            continue;
          }
          const escaped = text[index];
          const simpleEscape = { b: "\b", f: "\f", n: "\n", r: "\r", t: "\t", v: "\v", 0: "\0" }[escaped];
          if (simpleEscape !== undefined) {
            value += simpleEscape;
            advance();
            continue;
          }
          if (escaped === "x" && /^[0-9A-Fa-f]{2}$/.test(text.slice(index + 1, index + 3))) {
            value += String.fromCodePoint(Number.parseInt(text.slice(index + 1, index + 3), 16));
            advance();
            advance();
            advance();
            continue;
          }
          if (escaped === "u") {
            const braced = text[index + 1] === "{";
            const close = braced ? text.indexOf("}", index + 2) : -1;
            const digits = braced ? text.slice(index + 2, close) : text.slice(index + 1, index + 5);
            if ((braced ? close >= 0 : digits.length === 4) && /^[0-9A-Fa-f]+$/.test(digits)) {
              const codePoint = Number.parseInt(digits, 16);
              if (codePoint <= 0x10ffff) {
                value += String.fromCodePoint(codePoint);
                const target = braced ? close + 1 : index + 5;
                while (index < target) advance();
                continue;
              }
            }
          }
          value += escaped;
          advance();
          continue;
        }
        if (text[index] === quote) {
          advance();
          terminated = true;
          break;
        }
        if (text[index] === "\n" || text[index] === "\r") break;
        value += text[index];
        advance();
      }
      emit("string", value, start, startLine);
      if (!terminated) error("unterminated quoted string", start, startLine);
      continue;
    }

    if (character === "`") {
      scanTemplateText();
      continue;
    }

    if (IDENTIFIER_START.test(character)) {
      const start = index;
      const startLine = line;
      advance();
      while (index < text.length && IDENTIFIER_PART.test(text[index])) advance();
      emit("identifier", text.slice(start, index), start, startLine);
      continue;
    }

    if (character === "/" && canStartRegex(tokens)) {
      const start = index;
      const startLine = line;
      let inCharacterClass = false;
      let terminated = false;
      advance();
      while (index < text.length) {
        if (text[index] === "\\") {
          advance();
          if (index < text.length) advance();
          continue;
        }
        if (text[index] === "[") inCharacterClass = true;
        else if (text[index] === "]") inCharacterClass = false;
        else if (text[index] === "/" && !inCharacterClass) {
          advance();
          while (index < text.length && /[A-Za-z]/.test(text[index])) advance();
          terminated = true;
          break;
        } else if (text[index] === "\n" || text[index] === "\r") break;
        advance();
      }
      emit("regex", text.slice(start, index), start, startLine);
      if (!terminated) error("unterminated regular expression literal", start, startLine);
      continue;
    }

    const start = index;
    const startLine = line;
    const pair = text.slice(index, index + 2);
    const punctuation = ["=>", "?.", "??", "&&", "||", "==", "!=", "<=", ">=", "++", "--", "**"].includes(pair)
      ? pair
      : character;
    for (let consumed = 0; consumed < punctuation.length; consumed += 1) advance();
    emit("punctuation", punctuation, start, startLine);

    if (punctuation === "{") braceDepth += 1;
    if (punctuation === "}") {
      braceDepth -= 1;
      if (templateExpressions.length > 0 && braceDepth === templateExpressions.at(-1)) {
        templateExpressions.pop();
        scanTemplateText(false);
      }
    }
  }

  if (templateExpressions.length > 0) {
    errors.push({ message: "unterminated template expression", offset: text.length, line });
  }
  return { tokens, errors };
}

function significantTokens(tokens) {
  return tokens.filter(token => token.type !== "comment" && token.type !== "template" && token.type !== "regex");
}
function delimiterErrors(tokens) {
  const errors = [];
  const stack = [];
  const closingFor = new Map([["(", ")"], ["[", "]"], ["{", "}"], ["${", "}"]]);
  const openingFor = new Map([[")", "("], ["]", "["], ["}", "{"]]);
  for (const token of tokens) {
    if (closingFor.has(token.value)) {
      stack.push(token);
      continue;
    }
    if (!openingFor.has(token.value)) continue;
    const opening = stack.at(-1);
    const expected = opening && closingFor.get(opening.value);
    if (!opening || expected !== token.value) {
      errors.push({ message: `unmatched ${token.value}`, offset: token.start, line: token.line });
      continue;
    }
    stack.pop();
  }
  for (const opening of stack) {
    errors.push({ message: `unterminated ${opening.value}`, offset: opening.start, line: opening.line });
  }
  return errors;
}

function matchingClose(tokens, openIndex, openValue, closeValue) {
  let depth = 0;
  for (let index = openIndex; index < tokens.length; index += 1) {
    if (tokens[index].value === openValue) depth += 1;
    else if (tokens[index].value === closeValue) {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  return -1;
}

function statementEnd(tokens, start) {
  let braces = 0;
  let brackets = 0;
  let parentheses = 0;
  for (let index = start; index < tokens.length; index += 1) {
    const value = tokens[index].value;
    if (value === "{") braces += 1;
    else if (value === "}") braces -= 1;
    else if (value === "[") brackets += 1;
    else if (value === "]") brackets -= 1;
    else if (value === "(") parentheses += 1;
    else if (value === ")") parentheses -= 1;
    if (value === ";" && braces === 0 && brackets === 0 && parentheses === 0) return index;
  }
  return tokens.length;
}

function bindingDetails(tokens, start, end) {
  const bindings = [];
  let namespace = null;
  for (let index = start; index < end; index += 1) {
    if (tokens[index].value === "*" && tokens[index + 1]?.value === "as" && tokens[index + 2]?.type === "identifier") {
      namespace = tokens[index + 2].value;
      bindings.push({ imported: "*", local: namespace });
    }
    if (tokens[index].value === "{") {
      const close = matchingClose(tokens, index, "{", "}");
      if (close < 0 || close > end) break;
      for (let cursor = index + 1; cursor < close;) {
        if (tokens[cursor].type !== "identifier") {
          cursor += 1;
          continue;
        }
        const imported = tokens[cursor].value;
        let local = imported;
        if (["as", ":"].includes(tokens[cursor + 1]?.value) && tokens[cursor + 2]?.type === "identifier") {
          local = tokens[cursor + 2].value;
          cursor += 3;
        } else {
          cursor += 1;
        }
        bindings.push({ imported, local });
      }
      index = close;
    }
  }
  return { bindings, namespace };
}

function validImportClause(tokens, start, from) {
  let cursor = start;
  if (tokens[cursor]?.value === "type") cursor += 1;
  if (tokens[cursor]?.type === "identifier") {
    cursor += 1;
    if (cursor === from) return true;
    if (tokens[cursor]?.value !== ",") return false;
    cursor += 1;
  }
  if (tokens[cursor]?.value === "{") {
    return matchingClose(tokens, cursor, "{", "}") === from - 1;
  }
  if (tokens[cursor]?.value === "*") {
    return tokens[cursor + 1]?.value === "as"
      && tokens[cursor + 2]?.type === "identifier"
      && cursor + 3 === from;
  }
  return false;
}

function validExportClause(tokens, start, from) {
  let cursor = start;
  if (tokens[cursor]?.value === "type") cursor += 1;
  if (tokens[cursor]?.value === "{") {
    return matchingClose(tokens, cursor, "{", "}") === from - 1;
  }
  if (tokens[cursor]?.value === "*") {
    if (cursor + 1 === from) return true;
    return tokens[cursor + 1]?.value === "as"
      && tokens[cursor + 2]?.type === "identifier"
      && cursor + 3 === from;
  }
  return false;
}

function delimiterPairs(tokens) {
  const pairs = new Map();
  const stack = [];
  const closingFor = new Map([["(", ")"], ["[", "]"], ["{", "}"], ["${", "}"]]);
  for (let index = 0; index < tokens.length; index += 1) {
    const value = tokens[index].value;
    if (closingFor.has(value)) {
      stack.push(index);
      continue;
    }
    const open = stack.at(-1);
    if (open !== undefined && closingFor.get(tokens[open].value) === value) {
      stack.pop();
      pairs.set(open, index);
      pairs.set(index, open);
    }
  }
  return pairs;
}

function bindingNames(tokens, start, end) {
  const names = new Set();
  const modifiers = new Set(["type", "readonly", "public", "private", "protected"]);
  const topLevel = (from, to, wanted) => {
    let parentheses = 0;
    let brackets = 0;
    let braces = 0;
    for (let index = from; index < to; index += 1) {
      const value = tokens[index].value;
      if (wanted.has(value) && parentheses === 0 && brackets === 0 && braces === 0) return index;
      if (value === "(") parentheses += 1;
      else if (value === ")") parentheses -= 1;
      else if (value === "[") brackets += 1;
      else if (value === "]") brackets -= 1;
      else if (value === "{") braces += 1;
      else if (value === "}") braces -= 1;
    }
    return -1;
  };
  const collect = (from, to) => {
    while (tokens[from]?.value === "...") from += 1;
    if (from >= to) return;
    const opener = tokens[from]?.value;
    if (["{", "["].includes(opener)) {
      const closer = opener === "{" ? "}" : "]";
      const close = matchingClose(tokens, from, opener, closer);
      if (close < 0 || close >= to) return;
      let segment = from + 1;
      while (segment < close) {
        const comma = topLevel(segment, close, new Set([","]));
        const segmentEnd = comma < 0 ? close : comma;
        const equal = topLevel(segment, segmentEnd, new Set(["="]));
        const patternEnd = equal < 0 ? segmentEnd : equal;
        const colon = opener === "{" ? topLevel(segment, patternEnd, new Set([":"])) : -1;
        collect(colon < 0 ? segment : colon + 1, patternEnd);
        if (comma < 0) break;
        segment = comma + 1;
      }
      return;
    }
    for (let index = from; index < to; index += 1) {
      if (tokens[index]?.type === "identifier" && !modifiers.has(tokens[index].value)) {
        names.add(tokens[index].value);
        return;
      }
    }
  };
  collect(start, end);
  return names;
}

function parameterBindings(tokens, open, close) {
  const bindings = new Set();
  let segment = open + 1;
  let parentheses = 0;
  let brackets = 0;
  let braces = 0;
  for (let index = segment; index <= close; index += 1) {
    const value = tokens[index]?.value;
    const atBoundary = index === close || (value === "," && parentheses === 0 && brackets === 0 && braces === 0);
    if (atBoundary) {
      let patternEnd = index;
      let nestedParentheses = 0;
      let nestedBrackets = 0;
      let nestedBraces = 0;
      for (let cursor = segment; cursor < index; cursor += 1) {
        const current = tokens[cursor].value;
        if (current === "(") nestedParentheses += 1;
        else if (current === ")") nestedParentheses -= 1;
        else if (current === "[") nestedBrackets += 1;
        else if (current === "]") nestedBrackets -= 1;
        else if (current === "{") nestedBraces += 1;
        else if (current === "}") nestedBraces -= 1;
        else if (["=", ":"].includes(current) && nestedParentheses === 0 && nestedBrackets === 0 && nestedBraces === 0) {
          patternEnd = cursor;
          break;
        }
      }
      for (const name of bindingNames(tokens, segment, patternEnd)) bindings.add(name);
      segment = index + 1;
      continue;
    }
    if (value === "(") parentheses += 1;
    else if (value === ")") parentheses -= 1;
    else if (value === "[") brackets += 1;
    else if (value === "]") brackets -= 1;
    else if (value === "{") braces += 1;
    else if (value === "}") braces -= 1;
  }
  return bindings;
}
function arrowExpressionEnd(tokens, start) {
  const continuation = new Set([
    ".", "?.", "(", "[", "+", "-", "*", "/", "%", "**", "&&", "||", "??", "&", "|", "^", "<", ">", "<=", ">=", "==", "!=", "=", "?", ":", ",",
  ]);
  let parentheses = 0;
  let brackets = 0;
  let braces = 0;
  for (let index = start; index < tokens.length; index += 1) {
    const value = tokens[index].value;
    if (value === "(") parentheses += 1;
    if (index > start && tokens[index].line > tokens[index - 1].line
      && parentheses === 0 && brackets === 0 && braces === 0
      && !continuation.has(tokens[index - 1].value) && !continuation.has(value)) return index - 1;
    else if (value === ")") {
      if (parentheses === 0) return index - 1;
      parentheses -= 1;
    } else if (value === "[") brackets += 1;
    else if (value === "]") {
      if (brackets === 0) return index - 1;
      brackets -= 1;
    } else if (value === "{") braces += 1;
    else if (value === "}") {
      if (braces === 0) return index - 1;
      braces -= 1;
    } else if ([",", ";"].includes(value) && parentheses === 0 && brackets === 0 && braces === 0) {
      return index - 1;
    }
  }
  return tokens.length - 1;
}

function lexicalScopeModel(tokens, imports, errors) {
  const pairs = delimiterPairs(tokens);
  const scopes = [{ type: "module", start: 0, end: Math.max(0, tokens.length - 1), parent: -1, bindings: new Set() }];
  const functionBodyOpens = new Set();
  const addScope = (type, start, end, bindings = new Set()) => {
    const scope = { type, start, end, parent: 0, bindings };
    scopes.push(scope);
    return scopes.length - 1;
  };

  for (const imported of imports) {
    for (const binding of imported.bindings) scopes[0].bindings.add(binding.local);
  }

  for (let index = 0; index < tokens.length; index += 1) {
    if (tokens[index].value === "function") {
      let cursor = index + 1;
      if (tokens[cursor]?.value === "*") cursor += 1;
      const nameIndex = tokens[cursor]?.type === "identifier" ? cursor++ : -1;
      const open = tokens[cursor]?.value === "(" ? cursor : -1;
      const close = open >= 0 ? pairs.get(open) : undefined;
      const bodyOpen = close !== undefined && tokens[close + 1]?.value === "{" ? close + 1 : -1;
      const bodyClose = bodyOpen >= 0 ? pairs.get(bodyOpen) : undefined;
      if (open < 0 || close === undefined || bodyOpen < 0 || bodyClose === undefined) {
        errors.push({ message: "unsupported or malformed function scope", offset: tokens[index].start, line: tokens[index].line });
        continue;
      }
      const bindings = parameterBindings(tokens, open, close);
      const functionScope = addScope("function", index, bodyClose, bindings);
      functionBodyOpens.add(bodyOpen);
      if (nameIndex >= 0) {
        const previous = tokens[index - 1]?.value;
        const declaration = index === 0 || [";", "{", "}", "export", "default"].includes(previous)
          || (previous === "async" && (index === 1 || [";", "{", "}", "export", "default"].includes(tokens[index - 2]?.value)));
        if (declaration) scopes[functionScope].declarationName = { name: tokens[nameIndex].value, index };
        else scopes[functionScope].bindings.add(tokens[nameIndex].value);
      }
      continue;
    }

    if (tokens[index].value === "=>") {
      let bindings;
      let scopeStart;
      if (tokens[index - 1]?.type === "identifier") {
        bindings = new Set([tokens[index - 1].value]);
        scopeStart = index - 1;
      } else if (tokens[index - 1]?.value === ")") {
        const open = pairs.get(index - 1);
        if (open === undefined) {
          errors.push({ message: "unsupported or malformed arrow parameters", offset: tokens[index].start, line: tokens[index].line });
          continue;
        }
        bindings = parameterBindings(tokens, open, index - 1);
        scopeStart = open;
      } else {
        errors.push({ message: "unsupported or malformed arrow parameters", offset: tokens[index].start, line: tokens[index].line });
        continue;
      }
      const bodyStart = index + 1;
      if (tokens[bodyStart]?.value === "{") {
        const bodyEnd = pairs.get(bodyStart);
        if (bodyEnd === undefined) {
          errors.push({ message: "unsupported or malformed arrow body", offset: tokens[index].start, line: tokens[index].line });
          continue;
        }
        addScope("function", scopeStart, bodyEnd, bindings);
        functionBodyOpens.add(bodyStart);
      } else if (tokens[bodyStart]) {
        addScope("function", scopeStart, arrowExpressionEnd(tokens, bodyStart), bindings);
      } else {
        errors.push({ message: "unsupported or malformed arrow body", offset: tokens[index].start, line: tokens[index].line });
      }
    }
  }

  for (let index = 0; index < tokens.length; index += 1) {
    if (tokens[index].value !== "{" || functionBodyOpens.has(index)) continue;
    const close = pairs.get(index);
    if (close !== undefined) addScope("block", index, close);
  }

  const containingScope = (index, excluded = -1, functionOnly = false) => {
    let found = 0;
    let span = Number.POSITIVE_INFINITY;
    for (let candidate = 1; candidate < scopes.length; candidate += 1) {
      if (candidate === excluded || (functionOnly && scopes[candidate].type !== "function")) continue;
      const scope = scopes[candidate];
      if (scope.start <= index && index <= scope.end && scope.end - scope.start < span) {
        found = candidate;
        span = scope.end - scope.start;
      }
    }
    return found;
  };

  for (let index = 1; index < scopes.length; index += 1) scopes[index].parent = containingScope(scopes[index].start, index);
  for (let index = 1; index < scopes.length; index += 1) {
    const declaration = scopes[index].declarationName;
    if (declaration) scopes[scopes[index].parent].bindings.add(declaration.name);
    delete scopes[index].declarationName;
  }

  for (let index = 0; index < tokens.length; index += 1) {
    const kind = tokens[index].value;
    if (!["const", "let", "var"].includes(kind)) continue;
    let segment = index + 1;
    let parentheses = 0;
    let brackets = 0;
    let braces = 0;
    let inInitializer = false;
    for (let cursor = segment; cursor <= tokens.length; cursor += 1) {
      const value = tokens[cursor]?.value;
      const boundary = cursor === tokens.length
        || ([",", ";"].includes(value) && parentheses === 0 && brackets === 0 && braces === 0)
        || (value === ")" && parentheses === 0 && brackets === 0 && braces === 0);
      if (boundary) {
        if (!inInitializer) {
          const target = kind === "var" ? containingScope(index, -1, true) : containingScope(index);
          for (const name of bindingNames(tokens, segment, cursor)) scopes[target].bindings.add(name);
        }
        if (value !== ",") break;
        segment = cursor + 1;
        inInitializer = false;
        continue;
      }
      if (["=", "of", "in", ":"].includes(value) && parentheses === 0 && brackets === 0 && braces === 0) {
        if (!inInitializer) {
          const target = kind === "var" ? containingScope(index, -1, true) : containingScope(index);
          for (const name of bindingNames(tokens, segment, cursor)) scopes[target].bindings.add(name);
        }
        inInitializer = true;
        continue;
      }
      if (value === "(") parentheses += 1;
      else if (value === ")") parentheses -= 1;
      else if (value === "[") brackets += 1;
      else if (value === "]") brackets -= 1;
      else if (value === "{") braces += 1;
      else if (value === "}") braces -= 1;
    }
  }

  for (let index = 0; index < tokens.length; index += 1) {
    if (tokens[index].value === "class" && tokens[index + 1]?.type === "identifier") {
      const name = tokens[index + 1].value;
      const previous = tokens[index - 1]?.value;
      const declaration = index === 0 || [";", "{", "}", "export", "default"].includes(previous);
      const bodyOpen = tokens.findIndex((token, candidate) => candidate > index + 1 && token.value === "{");
      const bodyScope = scopes.findIndex(scope => scope.type === "block" && scope.start === bodyOpen);
      if (bodyOpen < 0 || bodyScope < 0) {
        errors.push({ message: "unsupported or malformed class scope", offset: tokens[index].start, line: tokens[index].line });
      } else if (declaration) {
        scopes[containingScope(index)].bindings.add(name);
        scopes[bodyScope].bindings.add(name);
      } else {
        scopes[bodyScope].bindings.add(name);
      }
    }
    if (tokens[index].value === "catch" && tokens[index + 1]?.value === "(") {
      const close = pairs.get(index + 1);
      const bodyOpen = close !== undefined && tokens[close + 1]?.value === "{" ? close + 1 : -1;
      const bodyScope = scopes.findIndex(scope => scope.type === "block" && scope.start === bodyOpen);
      if (close === undefined || bodyScope < 0) {
        errors.push({ message: "unsupported or malformed catch scope", offset: tokens[index].start, line: tokens[index].line });
      } else {
        const catchScope = addScope("block", index, scopes[bodyScope].end, bindingNames(tokens, index + 2, close));
        scopes[catchScope].parent = containingScope(index, catchScope);
        scopes[bodyScope].parent = catchScope;
      }
    }
  }

  return scopes.map(scope => ({ ...scope, bindings: [...scope.bindings] }));
}

export function identifierBindingScope(structure, index, name) {
  const scopes = structure.lexicalScopes ?? [];
  let current = 0;
  let span = Number.POSITIVE_INFINITY;
  for (let candidate = 0; candidate < scopes.length; candidate += 1) {
    const scope = scopes[candidate];
    if (scope.start <= index && index <= scope.end && scope.end - scope.start <= span) {
      current = candidate;
      span = scope.end - scope.start;
    }
  }
  while (current >= 0) {
    if (scopes[current]?.bindings.includes(name)) return current;
    current = scopes[current]?.parent ?? -1;
  }
  return -1;
}

export function isIdentifierLexicallyBound(structure, index, name) {
  return identifierBindingScope(structure, index, name) >= 0;
}

const FS_PATH_ARGUMENT_CALLS = new Set([
  "access", "accessSync", "appendFile", "appendFileSync", "chmod", "chmodSync", "chown", "chownSync",
  "copyFile", "copyFileSync", "createReadStream", "createWriteStream", "existsSync", "lstat", "lstatSync",
  "mkdir", "mkdirSync", "open", "openSync", "opendir", "opendirSync", "readFile", "readFileSync",
  "readlink", "readlinkSync", "realpath", "realpathSync", "rename", "renameSync", "rm", "rmSync",
  "stat", "statSync", "truncate", "truncateSync", "unlink", "unlinkSync", "watch", "writeFile", "writeFileSync",
]);
const PATH_CONSTRUCTION_CALLS = new Set(["join", "resolve"]);

function callNameBefore(tokens, openIndex) {
  const parts = [];
  let cursor = openIndex - 1;
  while (cursor >= 0) {
    const token = tokens[cursor];
    if (token.type === "identifier") {
      parts.unshift(token.value);
      cursor -= 1;
      if (tokens[cursor]?.value === "." || tokens[cursor]?.value === "?.") {
        cursor -= 1;
        continue;
      }
      break;
    }
    break;
  }
  return parts;
}

function argumentRanges(tokens, openIndex, closeIndex) {
  const ranges = [];
  let start = openIndex + 1;
  let depth = 0;
  for (let index = start; index < closeIndex; index += 1) {
    const value = tokens[index].value;
    if (["(", "[", "{"].includes(value)) depth += 1;
    else if ([")", "]", "}"].includes(value)) depth -= 1;
    else if (value === "," && depth === 0) {
      ranges.push([start, index]);
      start = index + 1;
    }
  }
  if (start < closeIndex) ranges.push([start, closeIndex]);
  return ranges;
}
function isImportMetaUrl(tokens, start, end) {
  return end - start === 5
    && tokens[start]?.value === "import"
    && tokens[start + 1]?.value === "."
    && tokens[start + 2]?.value === "meta"
    && tokens[start + 3]?.value === "."
    && tokens[start + 4]?.value === "url";
}


function staticPathExpression(tokens, start, end) {
  if (end - start === 1 && tokens[start]?.type === "string") return tokens[start].value;
  let open = -1;
  for (let index = start; index < end; index += 1) {
    if (tokens[index].value === "(") {
      open = index;
      break;
    }
  }
  if (open < 0) return null;
  const close = matchingClose(tokens, open, "(", ")");
  if (close !== end - 1) return null;
  const name = callNameBefore(tokens, open).at(-1);
  const ranges = argumentRanges(tokens, open, close);
  if (PATH_CONSTRUCTION_CALLS.has(name)) {
    const parts = ranges.map(([from, to]) => staticPathExpression(tokens, from, to));
    return parts.length > 0 && parts.every(part => part !== null) ? parts.join("/") : null;
  }
  if (name === "URL") {
    return tokens[start]?.value === "new"
      && ranges.length === 2
      && isImportMetaUrl(tokens, ...ranges[1])
      ? staticPathExpression(tokens, ...ranges[0])
      : null;
  }
  return null;
}

function structuralPathReferences(tokens) {
  const references = [];
  for (let open = 0; open < tokens.length; open += 1) {
    if (tokens[open].value !== "(") continue;
    const close = matchingClose(tokens, open, "(", ")");
    if (close < 0) continue;
    const name = callNameBefore(tokens, open).at(-1);
    const ranges = argumentRanges(tokens, open, close);
    if (ranges.length === 0) continue;
    if (FS_PATH_ARGUMENT_CALLS.has(name)) {
      const value = staticPathExpression(tokens, ...ranges[0]);
      if (value !== null) references.push(value);
    } else if (name === "URL") {
      const start = tokens[open - 2]?.value === "new" ? open - 2 : open - 1;
      const value = staticPathExpression(tokens, start, close + 1);
      if (value !== null) references.push(value);
    } else if (PATH_CONSTRUCTION_CALLS.has(name)) {
      const value = staticPathExpression(tokens, open - callNameBefore(tokens, open).length * 2 + 1, close + 1);
      if (value !== null) references.push(value);
    }
  }
  return references;
}

export function analyzeJavaScriptStructure(text) {
  const tokenized = tokenizeJavaScript(text);
  const tokens = significantTokens(tokenized.tokens);
  const imports = [];
  const pathReferences = structuralPathReferences(tokens);
  const errors = [...tokenized.errors, ...delimiterErrors(tokens)];

  const addCallImport = (kind, index) => {
    const open = index + 1;
    if (tokens[open]?.value !== "(") return false;
    const close = matchingClose(tokens, open, "(", ")");
    const argument = tokens[open + 1];
    if (close < 0) {
      errors.push({ message: `unterminated ${kind}()`, offset: tokens[index].start, line: tokens[index].line });
      return true;
    }
    if (argument?.type === "string" && (open + 2 === close || tokens[open + 2]?.value === ",")) {
      imports.push({ kind, specifier: argument.value, bindings: [], namespace: null });
    }
    return true;
  };

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.type !== "identifier") continue;
    if ([".", "?."].includes(tokens[index - 1]?.value)) continue;

    if (token.value === "require") {
      addCallImport("require", index);
      continue;
    }
    if (token.value === "import" && tokens[index + 1]?.value === ".") continue;
    if (token.value === "import" && addCallImport("dynamic-import", index)) continue;

    if (token.value === "import") {
      const end = statementEnd(tokens, index + 1);
      if (tokens[index + 1]?.type === "string") {
        if (end !== tokens.length && index + 2 !== end) {
          errors.push({ message: "malformed side-effect import", offset: token.start, line: token.line });
        } else {
          imports.push({ kind: "side-effect-import", specifier: tokens[index + 1].value, bindings: [], namespace: null });
        }
        continue;
      }
      const requireIndex = tokens.findIndex((candidate, candidateIndex) => candidateIndex > index && candidateIndex < end && candidate.value === "require");
      if (tokens[index + 1]?.type === "identifier" && tokens[index + 2]?.value === "=" && requireIndex > 0) continue;
      let from = -1;
      for (let cursor = index + 1; cursor < end; cursor += 1) {
        if (tokens[cursor].value === "from") {
          from = cursor;
          break;
        }
      }
      if (from < 0 || tokens[from + 1]?.type !== "string" || !validImportClause(tokens, index + 1, from)) {
        errors.push({ message: "malformed import declaration", offset: token.start, line: token.line });
        continue;
      }
      const details = bindingDetails(tokens, index + 1, from);
      if (tokens[index + 1]?.type === "identifier" && tokens[index + 1].value !== "type") {
        details.bindings.unshift({ imported: "default", local: tokens[index + 1].value });
      }
      imports.push({ kind: details.namespace ? "namespace-import" : details.bindings.length > 0 ? "bound-import" : "import", specifier: tokens[from + 1].value, ...details });
      continue;
    }

    if (token.value === "export") {
      const end = statementEnd(tokens, index + 1);
      let from = -1;
      for (let cursor = index + 1; cursor < end; cursor += 1) {
        if (tokens[cursor].value === "from") {
          from = cursor;
          break;
        }
      }
      if (from >= 0) {
        if (tokens[from + 1]?.type !== "string" || !validExportClause(tokens, index + 1, from)) {
          errors.push({ message: "malformed export-from declaration", offset: token.start, line: token.line });
        } else {
          imports.push({ kind: "export-from", specifier: tokens[from + 1].value, ...bindingDetails(tokens, index + 1, from) });
        }
      }
    }
  }

  const lexicalScopes = lexicalScopeModel(tokens, imports, errors);
  return { tokens, imports, pathReferences, errors, lexicalScopes };
}

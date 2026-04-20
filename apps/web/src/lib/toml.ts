export function parseTomlValue(valueStr: string): unknown {
  const v = valueStr.trim();
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1);
  }
  if (v === "true") return true;
  if (v === "false") return false;
  if (v.startsWith("[") && v.endsWith("]")) {
    const inner = v.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(",").map((s) => {
      const t = s.trim();
      if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
        return t.slice(1, -1);
      }
      return t;
    });
  }
  if (/^-?\d+$/.test(v)) return parseInt(v, 10);
  if (/^-?\d+\.\d+$/.test(v)) return parseFloat(v);
  return v;
}

export function parseToml(text: string): Record<string, unknown> {
  const lines = text.split("\n");
  const result: Record<string, unknown> = {};
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      i++;
      continue;
    }
    const eq = trimmed.indexOf("=");
    if (eq === -1) {
      i++;
      continue;
    }
    const key = trimmed.slice(0, eq).trim();
    let valueStr = trimmed.slice(eq + 1).trim();

    if (valueStr.startsWith('"""')) {
      let content = valueStr.slice(3);
      const endIndex = content.indexOf('"""');
      if (endIndex !== -1) {
        result[key] = content.slice(0, endIndex);
        i++;
        continue;
      }
      const parts: string[] = [];
      if (valueStr.length > 3) {
        parts.push(valueStr.slice(3));
      }
      i++;
      while (i < lines.length) {
        const l = lines[i];
        const end = l.indexOf('"""');
        if (end !== -1) {
          parts.push(l.slice(0, end));
          i++;
          break;
        }
        parts.push(l);
        i++;
      }
      result[key] = parts.join("\n");
      continue;
    }

    result[key] = parseTomlValue(valueStr);
    i++;
  }
  return result;
}

export function serializeToml(obj: Record<string, unknown>): string {
  const lines: string[] = [];
  for (const [key, value] of Object.entries(obj)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      const items = value.map((v) => `"${String(v).replace(/"/g, '\\"')}"`).join(", ");
      lines.push(`${key} = [${items}]`);
    } else if (typeof value === "string") {
      if (value.includes("\n") || value.includes('"')) {
        lines.push(`${key} = """\n${value}\n"""`);
      } else {
        lines.push(`${key} = "${value}"`);
      }
    } else if (typeof value === "number" || typeof value === "boolean") {
      lines.push(`${key} = ${value}`);
    } else {
      lines.push(`${key} = "${String(value).replace(/"/g, '\\"')}"`);
    }
  }
  return lines.join("\n");
}

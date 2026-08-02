const VARIABLE_PATTERN = /\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g;

export function extractTemplateVariables(text: string): string[] {
  const matches = new Set<string>();
  for (const match of text.matchAll(VARIABLE_PATTERN)) {
    matches.add(match[1]!);
  }
  return [...matches].sort();
}

export function validatePromptVariables(
  systemPrompt: string,
  userTemplate: string,
  declaredVariables: string[],
): { valid: boolean; errors: string[] } {
  const used = new Set([
    ...extractTemplateVariables(systemPrompt),
    ...extractTemplateVariables(userTemplate),
  ]);
  const declared = new Set(declaredVariables);
  const errors: string[] = [];

  for (const variable of used) {
    if (!declared.has(variable)) {
      errors.push(`Placeholder {{${variable}}} is used but not declared.`);
    }
  }

  for (const variable of declared) {
    if (!used.has(variable)) {
      errors.push(`Declared variable "${variable}" is not used in templates.`);
    }
  }

  return { valid: errors.length === 0, errors };
}

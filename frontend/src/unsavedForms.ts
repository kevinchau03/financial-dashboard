// Shared registration keeps route and inline cancellation protection in one owner.
export const unsavedForms = new Map<HTMLFormElement, () => { dirty: boolean; busy: boolean }>()

export function formSnapshot(form: HTMLFormElement) {
  return JSON.stringify(Array.from(form.elements).flatMap(field => {
    if (field instanceof HTMLInputElement) return [[field.name || field.id, field.type === 'checkbox' ? field.checked : field.value]]
    if (field instanceof HTMLTextAreaElement || field instanceof HTMLSelectElement) return [[field.name, field.value]]
    return []
  }))
}

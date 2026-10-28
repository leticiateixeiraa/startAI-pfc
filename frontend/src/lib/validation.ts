// Regras de validação dos formulários, iguais às do backend (app/auth/schemas.py).
// O front valida para dar retorno imediato; quem garante a regra é a API.

export const NAME_MIN = 2;
export const NAME_MAX = 100;
export const PASSWORD_MIN = 8;
export const PASSWORD_MAX_BYTES = 72; // limite do bcrypt

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateName(value: string): string | null {
  const name = value.trim().replace(/\s+/g, " ");
  if (!name) return "Informe seu nome.";
  if (name.length < NAME_MIN) return `O nome precisa ter pelo menos ${NAME_MIN} caracteres.`;
  if (name.length > NAME_MAX) return `O nome pode ter no máximo ${NAME_MAX} caracteres.`;
  if (!/\p{L}/u.test(name)) return "O nome precisa conter letras.";
  return null;
}

export function validateEmail(value: string): string | null {
  const email = value.trim();
  if (!email) return "Informe seu e-mail.";
  if (!EMAIL_PATTERN.test(email)) return "Digite um e-mail válido, como nome@exemplo.com.";
  return null;
}

export type PasswordCheck = { label: string; ok: boolean };

export function passwordChecks(password: string): PasswordCheck[] {
  return [
    { label: `Pelo menos ${PASSWORD_MIN} caracteres`, ok: password.length >= PASSWORD_MIN },
    { label: "Letras e números", ok: /\p{L}/u.test(password) && /\d/.test(password) },
    { label: "Um caractere especial (ex: ! @ # $ %)", ok: /[^\p{L}\d]/u.test(password) },
  ];
}

export function validatePassword(password: string): string | null {
  if (!password) return "Informe uma senha.";
  if (new TextEncoder().encode(password).length > PASSWORD_MAX_BYTES) {
    return "A senha pode ter no máximo 72 caracteres.";
  }
  const failed = passwordChecks(password).find((check) => !check.ok);
  return failed ? `A senha precisa ter: ${failed.label.toLowerCase()}.` : null;
}

export function validatePasswordConfirmation(password: string, confirmation: string): string | null {
  if (!confirmation) return "Confirme a senha.";
  if (password !== confirmation) return "As senhas não coincidem.";
  return null;
}

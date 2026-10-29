// feat(admin): proteção das telas /admin no front.
// É só para a experiência do usuário: a proteção de verdade é o 403 do back-end.
import { redirect } from "@tanstack/react-router";
import { isCurrentUserAdmin } from "@/services/authService";

export async function requireAdminBeforeLoad() {
  if (!localStorage.getItem("access_token")) {
    throw redirect({ to: "/" });
  }
  if (!(await isCurrentUserAdmin())) {
    throw redirect({ to: "/home" });
  }
}

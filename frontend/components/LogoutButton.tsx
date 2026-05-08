"use client";

import { useRouter } from "next/navigation";
import { Button } from "@thomasbrunner-spec/design-system";
import { createClient } from "@/lib/supabase/client";

export function LogoutButton() {
  const router = useRouter();
  const supabase = createClient();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  };

  return (
    <Button variant="ghost" size="sm" onClick={handleLogout}>
      Sign out
    </Button>
  );
}

/**
 * TypeScript mirror of backend/app/schemas/consultant.py — keep in sync.
 */

export interface Consultant {
  id: string;
  name: string;
  titel: string | null;
  tel: string | null;
  email: string | null;
  created_at: string;
}

export interface ConsultantCreate {
  name: string;
  titel: string | null;
  tel: string | null;
  email: string | null;
}

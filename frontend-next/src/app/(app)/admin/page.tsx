import { auth, currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { apiClient } from "@/lib/api";
import AdminPanel from "./AdminPanel";

const ADMIN_EMAILS = ["diadamflow@gmail.com"];

export default async function AdminPage() {
  const { getToken } = await auth();
  const user = await currentUser();

  const email = user?.emailAddresses?.[0]?.emailAddress ?? "";
  if (!ADMIN_EMAILS.includes(email.toLowerCase())) {
    redirect("/dashboard");
  }

  const token = await getToken();
  let dashData = { total_users: 0, total_analyses: 0, success_analyses: 0, pending_analyses: 0 };
  let usersData: { total: number; users: AdminUser[] } = { total: 0, users: [] };
  let analysesData: { total: number; analyses: AdminAnalysis[] } = { total: 0, analyses: [] };

  if (token) {
    try {
      [dashData, usersData, analysesData] = await Promise.all([
        apiClient(token).get<typeof dashData>("/admin/dashboard"),
        apiClient(token).get<typeof usersData>("/admin/all-users?per_page=100"),
        apiClient(token).get<typeof analysesData>("/admin/all-analyses?per_page=100"),
      ]);
    } catch (e) {
      console.error("Admin fetch error:", e);
    }
  }

  return (
    <AdminPanel
      token={token ?? ""}
      dash={dashData}
      users={usersData.users}
      analyses={analysesData.analyses}
    />
  );
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  plan: string;
  analyses_this_month: number;
  clerk_id: string | null;
  created_at: string;
}

export interface AdminAnalysis {
  id: number;
  company_name: string;
  user_email: string;
  user_id: number;
  report_year: number | null;
  score_global: number | null;
  status: string;
  created_at: string;
}

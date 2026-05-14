import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import AppLayout from "@/components/AppLayout";

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  return <AppLayout>{children}</AppLayout>;
}

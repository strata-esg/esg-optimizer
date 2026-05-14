import Sidebar from "./Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#F7F2E8]">
      <Sidebar />
      {/* Main content — offset sidebar width */}
      <main className="flex-1 ml-64 p-8 min-h-screen">
        <div className="w-full">
          {children}
        </div>
      </main>
    </div>
  );
}

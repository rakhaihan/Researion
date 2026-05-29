import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function Layout() {
  return (
    <div className="min-h-screen lg:flex">
      <Sidebar />
      <main className="flex-1">
        <div className="border-b border-slate-200 bg-white px-6 py-4 lg:hidden">
          <h1 className="text-lg font-semibold text-slate-900">Researion</h1>
        </div>
        <div className="mx-auto max-w-6xl px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

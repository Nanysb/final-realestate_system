// src/pages/Dashboard.jsx
import { useEffect, useState } from "react";
import axios from "../api/axios";

export default function Dashboard() {
  const [stats, setStats] = useState({ companies: 0, projects: 0, units: 0 });

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await axios.get("/admin/dashboard"); // لازم تضيف هذا endpoint في Flask
        if (res.data.ok) setStats(res.data.stats);
      } catch (err) {
        console.log(err);
      }
    }
    fetchStats();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">لوحة التحكم</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 bg-white rounded shadow">الشركات: {stats.companies}</div>
        <div className="p-4 bg-white rounded shadow">المشاريع: {stats.projects}</div>
        <div className="p-4 bg-white rounded shadow">الوحدات: {stats.units}</div>
      </div>
    </div>
  );
}

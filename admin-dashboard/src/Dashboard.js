import { useEffect, useState } from "react";
import { getCompanies } from "./api";

export default function Dashboard() {
  const [companies, setCompanies] = useState([]);

  useEffect(() => {
    async function fetchData() {
      const data = await getCompanies();
      if(data.ok) setCompanies(data.companies);
    }
    fetchData();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h2>الشركات</h2>
      <ul>
        {companies.map(c => (
          <li key={c.id}>{c.name} - {c.slug}</li>
        ))}
      </ul>
    </div>
  );
}

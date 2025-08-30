import { useState } from "react";
import { loginAdmin } from "./api";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    const res = await loginAdmin(username, password);
    if(res.ok) onLogin();
    else alert(res.error);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>تسجيل دخول الأدمن</h2>
      <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
      <button onClick={handleLogin}>دخول</button>
    </div>
  );
}

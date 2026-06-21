# NoorTime: Production Architecture & Security Blueprint (Final Version)

Yeh document tumhare poore backend, frontend, aur security architecture ka Master Plan hai.

---

## 1. Core Architecture Strategy (Monolithic Backend + API Gateway/BFF)

*   **Central API Gateway (BFF):** Saare UIs (Web App, Mobile, Admin, Agent) sabse pehle API Gateway (BFF) par aayenge. Gateway JWT token verify karega aur sirf valid traffic ko internal Main API tak bhejega.

---

## 2. Docker Container Setup & Network Rules (7 Containers)

**PUBLIC CONTAINERS (Inhe public internet se dekha ja sakta hai):**
1.  **Container 3 (API Gateway / BFF):** Sabhi public API requests handle karega.
2.  **Container 4 (Landing Page):** Main website UI.
3.  **Container 5 (User Web App):** Browser app UI.
4.  **Container 6 (Super Admin UI):** Admin Dashboard UI.
5.  **Container 7 (Marketing Agent UI):** Agent Dashboard UI.

**STRICTLY PRIVATE CONTAINERS (Inka koi Domain/Sub-domain NAHI hoga):**
6.  **Container 1 (Database - PostgreSQL/MySQL):** 
    *   *Security Rule:* Iska koi domain nahi hoga. Iska port (e.g., 5432) public internet par expose nahi hoga. Yeh sirf Docker ke internal network par `db-server:5432` ke naam se jana jayega.
7.  **Container 2 (Main Backend API - Nuitka Compiled):** 
    *   *Security Rule:* Iska bhi koi public domain nahi hoga. BFF server internally isko `main-backend:8000` (Docker internal IP) ke zariye call karega.

---

## 3. Domain aur Sub-domain Routing (Only for Public Containers)

*   **`noortime.com`** -> Route to Container 4 (Landing Page)
*   **`app.noortime.com`** -> Route to Container 5 (User Web App)
*   **`admin.noortime.com`** -> Route to Container 6 (Super Admin UI)
*   **`agent.noortime.com`** -> Route to Container 7 (Marketing Agent UI)
*   **`api.noortime.com`** -> Route to Container 3 (API Gateway / BFF)

---

## 4. Compilation Strategy (Kise Nuitka karna hai aur kise nahi?)

*   **Main Backend API (Container 2):** **YES.** Kyunki yeh tumne Python mein likha hai, isko Nuitka se C++ mein compile karke `.so/.exe` banana hai.
*   **API Gateway/BFF (Container 3):** **YES** (Agar Python mein banaya hai toh). Agar Node.js mein banaya hai toh Nuitka kaam nahi karega, usme Javascript obfuscator use karna hoga.
*   **Database (Container 1):** **NO.** Database (jaise Postgres ya MySQL) hum khud code nahi karte. Wo pehle se hi highly optimized C/C++ mein compile hokar Docker image ke roop mein aate hain. DB ki security uske passwords aur upar bataye gaye "Private Network Rules" se hoti hai.
*   **Frontend UIs (Containers 4,5,6,7):** **NO.** Inme HTML/JS/React hota hai. Inko Nuitka se compile nahi kiya jata. Inko build karte waqt 'Webpack' ya 'Vite' jaisa tool inka code minify (chota aur complex) kar deta hai jise 'Minification' kehte hain.

---

## 5. Mobile App & Web Security

1.  **Mobile App:** ProGuard (Code Obfuscation) aur Certificate Pinning active karni hai.
2.  **Web App/Panels:** Cookies aur JWT tokens ko hamesha 'HttpOnly' aur 'Secure' flags ke sath bhejna hai.
3.  **String Encryption:** API URLs ko app ke andar encrypt karke rakhna hai.

---

## 6. Rate Limiting aur WAF
*   **Gateway Protection:** API Gateway (`api.noortime.com`) par Rate Limiting lagani hai.
*   **Production `/docs` Disable:** API docs production mein strictly disable hone chahiye.

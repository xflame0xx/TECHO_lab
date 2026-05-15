import React from "react";
import ReactDOM from "react-dom/client";
import "bootstrap/dist/css/bootstrap.min.css";

import "./styles/base.css";
import "./styles/auth.css";
import "./styles/vacancies.css";
import "./styles/vacancy.css";
import "./styles/applications.css";
import "./styles/application.css";
import "./styles/cabinet.css";
import "./index.css";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

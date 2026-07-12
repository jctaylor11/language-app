import { GoogleLogin } from "@react-oauth/google";
import type { CredentialResponse } from "@react-oauth/google";
import { useNavigate } from "react-router";

import { authenticateWithGoogleToken } from "../api";
import { useAuth } from "../AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    const credential = credentialResponse.credential;
    if (!credential) return;

    await authenticateWithGoogleToken(credential);
    login();
    navigate("/vocab", { replace: true });
  };
  return (
    <GoogleLogin
      onSuccess={(credentialResponse) => handleSuccess(credentialResponse)}
      onError={() => console.log("Login failed")}
    />
  );
}

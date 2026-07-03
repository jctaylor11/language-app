import { GoogleLogin } from "@react-oauth/google";
import type { CredentialResponse } from "@react-oauth/google";

import { getJWTFromGoogleToken } from "../api";

export default function Login() {
  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    const credential = credentialResponse.credential;

    if (!credential) return;

    const jwt = await getJWTFromGoogleToken(credential);
    console.log("JWT Response:", jwt); // Checkpoint that its pulling JWT placeholder
  };
  return (
    <GoogleLogin
      onSuccess={(credentialResponse) => handleSuccess(credentialResponse)}
      onError={() => console.log("Login failed")}
    />
  );
}

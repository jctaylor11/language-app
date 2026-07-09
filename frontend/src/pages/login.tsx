import { GoogleLogin } from "@react-oauth/google";
import type { CredentialResponse } from "@react-oauth/google";

import { getJWTFromGoogleToken } from "../api";
import { useAuth } from "../AuthContext";

export default function Login() {
  const { login } = useAuth();

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    const credential = credentialResponse.credential;

    if (!credential) return;

    const jwt = await getJWTFromGoogleToken(credential);

    login(jwt);
  };
  return (
    <GoogleLogin
      onSuccess={(credentialResponse) => handleSuccess(credentialResponse)}
      onError={() => console.log("Login failed")}
    />
  );
}

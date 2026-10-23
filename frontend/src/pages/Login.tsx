import { GoogleLogin } from "@react-oauth/google";
import type { CredentialResponse } from "@react-oauth/google";
import { Link, useNavigate } from "react-router";

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

  const buttonScale = 1.25; // Google caps its button at 40px tall, so scale it up to make it the obvious action
  const buttonWidth = Math.min(window.innerWidth - 48, 400) / buttonScale; // Google's button is a fixed-pixel iframe that CSS can't size, so match the column width before scaling. 48: wrapper px-6, 400: column max-w

  // fixed rather than h-full so it centres on the window, not on <main> below the nav. pointer-events-none keeps the nav clickable underneath
  return (
    <div className="fixed inset-0 px-6 flex items-center justify-center pointer-events-none">
      <div className="w-full max-w-[400px] flex flex-col items-center gap-10 text-center pointer-events-auto">
        <div className="flex flex-col items-center gap-4">
          <h1 className="text-7xl font-semibold">상기</h1>
          <p className="text-lg text-balance text-[#5B636E]">
            Continue with your Google account to get started.
          </p>
        </div>
        {/* Tighter gap than the outer column: the legal line is a footnote to the button */}
        <div className="w-full flex flex-col items-center gap-5">
          {/* Fixed height reserves the scaled button's space, since transforms don't affect layout, and stops the layout jumping when the iframe loads */}
          <div
            className="w-full flex items-center justify-center"
            style={{ height: 40 * buttonScale }}
          >
            <div style={{ transform: `scale(${buttonScale})` }}>
              <GoogleLogin
                onSuccess={(credentialResponse) => handleSuccess(credentialResponse)}
                onError={() => console.log("Login failed")}
                shape="pill"
                logo_alignment="left"
                width={buttonWidth}
              />
            </div>
          </div>
          <p className="text-sm text-balance text-[#5B636E]">
            By continuing, you agree to the{" "}
            <Link to="/terms" className="text-[#3B4CCA] underline">
              Terms
            </Link>{" "}
            and{" "}
            <Link to="/privacy" className="text-[#3B4CCA] underline">
              Privacy Policy
            </Link>{" "}
            (placeholders for now).
          </p>
        </div>
      </div>
    </div>
  );
}

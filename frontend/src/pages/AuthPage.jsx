import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AuthPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [isLogin, setIsLogin] = useState(true);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setSubmitting(true);

    try {
      if (isLogin) {
        await login(email, password);
        navigate("/", { replace: true });
      } else {
        await register(name, email, password);

        setSuccess(
          "Account created successfully. You can now sign in."
        );

        setIsLogin(true);
        setPassword("");
      }
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setError("");
    setSuccess("");
    setPassword("");
  };

  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <div className="mx-auto flex min-h-screen max-w-7xl items-center justify-center px-6 py-12">
        <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-outline-variant bg-surface-container-lowest shadow-sm md:grid-cols-2">

          {/* Left panel */}
          <div className="hidden flex-col justify-between bg-primary p-10 text-white md:flex">
            <div>
              <div className="mb-8 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/15">
                  <span className="material-symbols-outlined">
                    auto_stories
                  </span>
                </div>

                <span className="text-xl font-semibold">
                  ScholarPulse
                </span>
              </div>

              <p className="mb-3 text-sm font-medium uppercase tracking-wider text-white/70">
                Research workspace
              </p>

              <h1 className="max-w-md text-4xl font-semibold leading-tight">
                Turn research into clearer insights.
              </h1>

              <p className="mt-5 max-w-md text-sm leading-6 text-white/75">
                Search papers, organize your research, compare studies,
                and explore your literature from one focused workspace.
              </p>
            </div>

            <div className="flex items-center gap-2 text-sm text-white/65">
              <span className="material-symbols-outlined text-[18px]">
                verified
              </span>
              Your research workspace
            </div>
          </div>

          {/* Form panel */}
          <div className="p-8 sm:p-10">
            <div className="mx-auto max-w-md">

              <div className="mb-8 md:hidden">
                <div className="mb-5 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white">
                    <span className="material-symbols-outlined">
                      auto_stories
                    </span>
                  </div>

                  <span className="text-xl font-semibold">
                    ScholarPulse
                  </span>
                </div>
              </div>

              <div className="mb-8">
                <h2 className="text-2xl font-semibold">
                  {isLogin ? "Welcome back" : "Create your account"}
                </h2>

                <p className="mt-2 text-sm text-on-surface-variant">
                  {isLogin
                    ? "Sign in to continue your research."
                    : "Create a workspace for your research."}
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">

                {!isLogin && (
                  <div>
                    <label className="mb-2 block text-sm font-medium">
                      Name
                    </label>

                    <input
                      type="text"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      placeholder="Your name"
                      required
                      className="w-full rounded-lg border border-outline-variant bg-surface px-4 py-3 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                    />
                  </div>
                )}

                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Email
                  </label>

                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    required
                    className="w-full rounded-lg border border-outline-variant bg-surface px-4 py-3 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Password
                  </label>

                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Enter your password"
                    required
                    minLength={6}
                    className="w-full rounded-lg border border-outline-variant bg-surface px-4 py-3 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/10"
                  />
                </div>

                {error && (
                  <div className="flex gap-2 rounded-lg border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
                    <span className="material-symbols-outlined text-[18px]">
                      error
                    </span>

                    <p>{error}</p>
                  </div>
                )}

                {success && (
                  <div className="flex gap-2 rounded-lg border border-green-500/20 bg-green-500/5 px-4 py-3 text-sm text-green-700">
                    <span className="material-symbols-outlined text-[18px]">
                      check_circle
                    </span>

                    <p>{success}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submitting && (
                    <span className="material-symbols-outlined animate-spin text-[18px]">
                      progress_activity
                    </span>
                  )}

                  {submitting
                    ? "Please wait..."
                    : isLogin
                      ? "Sign in"
                      : "Create account"}
                </button>
              </form>

              <div className="mt-7 text-center text-sm text-on-surface-variant">
                <span>
                  {isLogin
                    ? "Don't have an account?"
                    : "Already have an account?"}
                </span>

                <button
                  type="button"
                  onClick={switchMode}
                  className="ml-1 font-medium text-secondary hover:underline"
                >
                  {isLogin ? "Create one" : "Sign in"}
                </button>
              </div>

            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
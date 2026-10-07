import { useEffect, useRef, useState } from "react";
import { getTelegramWidgetConfig } from "../api";
import type { TelegramConnectPayload } from "../api";
import { Brand } from "./Brand";
import { Icon } from "./Icon";
import { ui } from "../ui";

declare global {
  interface Window {
    onTelegramAuth?: (user: TelegramConnectPayload) => void;
  }
}

interface TelegramSetupPageProps {
  busy: boolean;
  error?: string;
  success?: string;
  onBack: () => void;
  onConnect: (payload: TelegramConnectPayload) => Promise<void>;
  onDisconnect: () => Promise<void>;
}

export function TelegramSetupPage({
  busy,
  error,
  success,
  onBack,
  onConnect,
  onDisconnect,
}: TelegramSetupPageProps) {
  const widgetRef = useRef<HTMLDivElement>(null);
  const onConnectRef = useRef(onConnect);
  const [botUsername, setBotUsername] = useState("");
  const [widgetError, setWidgetError] = useState("");

  useEffect(() => {
    onConnectRef.current = onConnect;
  }, [onConnect]);

  useEffect(() => {
    const previousHandler = window.onTelegramAuth;
    window.onTelegramAuth = (user) => {
      void onConnectRef.current(user).catch(() => undefined);
    };
    let cancelled = false;
    void getTelegramWidgetConfig()
      .then((config) => {
        if (!cancelled) setBotUsername(config.bot_username.replace(/^@/, ""));
      })
      .catch(() => {
        if (!cancelled)
          setWidgetError("Telegram sign-in is temporarily unavailable.");
      });

    return () => {
      cancelled = true;
      if (previousHandler) window.onTelegramAuth = previousHandler;
      else delete window.onTelegramAuth;
    };
  }, []);

  useEffect(() => {
    const mount = widgetRef.current;
    if (!mount || !botUsername) return;

    mount.replaceChildren();
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.dataset.telegramLogin = botUsername;
    script.dataset.size = "large";
    script.dataset.userpic = "false";
    script.dataset.requestAccess = "write";
    script.dataset.onauth = "onTelegramAuth(user)";
    mount.append(script);

    return () => script.remove();
  }, [botUsername]);

  return (
    <main className={ui.telegramPage}>
      <div className={ui.telegramShell}>
        <header className={ui.telegramHeader}>
          <button className={ui.textButton} onClick={onBack} type="button">
            ← Back to workspace
          </button>
          <Brand />
        </header>

        <section className={ui.telegramLayout}>
          <div className={ui.telegramIntro}>
            <div className={ui.telegramMark} aria-hidden="true">
              <Icon name="send" size={23} />
            </div>
            <div>
              <h1 className={ui.telegramTitle}>
                Your workflow, now on Telegram.
              </h1>
              <p className={ui.telegramCopy}>
                Link the Telegram account you use for work. Messages sent to
                your DocPilot bot use the same doctor identity and memory scope
                as this workspace.
              </p>
            </div>
            <p className={ui.telegramTrust}>
              <Icon name="lock" size={17} />
              Telegram verifies your account before DocPilot links it to this
              workspace.
            </p>
          </div>

          <section
            aria-labelledby="telegram-connect-title"
            className={ui.telegramPanel}
          >
            <div className={ui.telegramPanelHeading}>
              <h2
                className="text-xl font-semibold tracking-tight"
                id="telegram-connect-title"
              >
                Link your account
              </h2>
              <p className="mt-2 text-sm text-ink-quiet">
                Two quick steps, then you can message your bot.
              </p>
            </div>

            {error && (
              <div className={ui.formAlert} role="alert">
                <span>{error}</span>
              </div>
            )}
            {success && (
              <div
                className={`${ui.inlineAlert} text-green-deep`}
                role="status"
              >
                <span>{success}</span>
              </div>
            )}
            {widgetError && (
              <p className={ui.formAlert} role="alert">
                {widgetError}
              </p>
            )}

            <ol
              aria-label="Connect Telegram in two steps"
              className={ui.telegramSteps}
            >
              <li className={ui.telegramStep}>
                <span aria-hidden="true" className={ui.telegramStepNumber}>
                  1
                </span>
                <div className={ui.telegramStepContent}>
                  <h3 className="font-semibold">
                    Verify your Telegram account
                  </h3>
                  <p className="text-sm leading-relaxed text-ink-soft">
                    Use Telegram’s sign-in button to securely link this
                    workspace.
                  </p>
                  {!widgetError && !botUsername && (
                    <p className="text-sm text-ink-quiet" role="status">
                      Loading Telegram sign-in…
                    </p>
                  )}
                  <div
                    aria-busy={busy}
                    aria-label="Sign in with Telegram"
                    className="min-h-12"
                    ref={widgetRef}
                    role="group"
                  />
                  {busy && (
                    <p className="text-sm text-ink-quiet" role="status">
                      Linking your account…
                    </p>
                  )}
                </div>
              </li>
              <li className={ui.telegramStep}>
                <span aria-hidden="true" className={ui.telegramStepNumber}>
                  2
                </span>
                <div className={ui.telegramStepContent}>
                  <h3 className="font-semibold">Open your DocPilot bot</h3>
                  <p className="text-sm leading-relaxed text-ink-soft">
                    Once linked, open the bot to start a conversation.
                  </p>
                  {botUsername && (
                    <a
                      className={ui.primaryButton}
                      href={`https://t.me/${botUsername}`}
                      rel="noreferrer"
                      target="_blank"
                    >
                      Open @{botUsername} in Telegram
                      <Icon name="arrow" size={16} />
                    </a>
                  )}
                </div>
              </li>
            </ol>

            <div className={ui.telegramFooter}>
              <button
                className={ui.textButton}
                disabled={busy}
                onClick={() => void onDisconnect()}
                type="button"
              >
                Disconnect Telegram
              </button>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}

export type UTMKey = "utm_source" | "utm_medium" | "utm_campaign" | "utm_term" | "utm_content";

export type UTMParams = Partial<Record<UTMKey, string>> & {
  initial_referrer?: string;
  landing_path?: string;
};

const UTM_KEYS: readonly UTMKey[] = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
];

export function captureUTMFromLocation(location: Location = window.location): UTMParams {
  const params = new URLSearchParams(location.search);
  const utm: UTMParams = {};

  for (const key of UTM_KEYS) {
    const value = params.get(key);
    if (value) {
      utm[key] = value;
      localStorage.setItem(key, value);
    }
  }

  // Capture once (first-touch) if present.
  if (!localStorage.getItem("initial_referrer")) {
    const referrer = document.referrer || "";
    if (referrer) {
      localStorage.setItem("initial_referrer", referrer);
      utm.initial_referrer = referrer;
    }
  }

  if (!localStorage.getItem("landing_path")) {
    localStorage.setItem("landing_path", location.pathname);
    utm.landing_path = location.pathname;
  }

  return utm;
}

export function getStoredUTM(): UTMParams {
  const utm: UTMParams = {};

  for (const key of UTM_KEYS) {
    const value = localStorage.getItem(key);
    if (value) utm[key] = value;
  }

  const initialReferrer = localStorage.getItem("initial_referrer");
  if (initialReferrer) utm.initial_referrer = initialReferrer;

  const landingPath = localStorage.getItem("landing_path");
  if (landingPath) utm.landing_path = landingPath;

  return utm;
}


// src/locales/index.js
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// místo `import GLOBAL from "./translations_global"`
import * as GLOBAL from "./translations_global";
import * as HOME from "./translations_index";
import * as KONTAKT from "./translations_kontakt";
import * as RESTAURACE from "./translations_restaurace";
import * as GALERIE from "./translations_galerie";
import * as SVATBY from "./translations_svatby";
import * as UBYTOVANI from "./translations_ubytovani";
import * as BALICKY from "./translations_balicky";
import * as CENIK from "./translation_cenik";
import * as REZERVACE from "./translations_rezervace";
import * as POKOJE from "./translations_pokoje";
import * as GDPR from "./translations_gdpr";

const SUPPORTED_LANGUAGES = ["cs", "en", "de", "pl"];

function getNamespaceResource(moduleExports, lang) {
  if (moduleExports?.[lang]) {
    return moduleExports[lang];
  }

  const wrapper = Object.values(moduleExports || {}).find(
    (value) =>
      value &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      Object.prototype.hasOwnProperty.call(value, lang),
  );

  return wrapper?.[lang] || {};
}

function getInitialLanguage() {
  if (typeof window === "undefined") return "cs";
  const saved = window.localStorage.getItem("appLanguage");
  return SUPPORTED_LANGUAGES.includes(saved) ? saved : "cs";
}

const resources = {
  cs: {
    global: getNamespaceResource(GLOBAL, "cs"),
    home: getNamespaceResource(HOME, "cs"),
    kontakt: getNamespaceResource(KONTAKT, "cs"),
    restaurace: getNamespaceResource(RESTAURACE, "cs"),
    galerie: getNamespaceResource(GALERIE, "cs"),
    svatby: getNamespaceResource(SVATBY, "cs"),
    ubytovani: getNamespaceResource(UBYTOVANI, "cs"),
    balicky: getNamespaceResource(BALICKY, "cs"),
    cenik: getNamespaceResource(CENIK, "cs"),
    rezervace: getNamespaceResource(REZERVACE, "cs"),
    pokoje: getNamespaceResource(POKOJE, "cs"),
    gdpr: getNamespaceResource(GDPR, "cs"),
  },
  en: {
    global: getNamespaceResource(GLOBAL, "en"),
    home: getNamespaceResource(HOME, "en"),
    kontakt: getNamespaceResource(KONTAKT, "en"),
    restaurace: getNamespaceResource(RESTAURACE, "en"),
    galerie: getNamespaceResource(GALERIE, "en"),
    svatby: getNamespaceResource(SVATBY, "en"),
    ubytovani: getNamespaceResource(UBYTOVANI, "en"),
    balicky: getNamespaceResource(BALICKY, "en"),
    cenik: getNamespaceResource(CENIK, "en"),
    rezervace: getNamespaceResource(REZERVACE, "en"),
    pokoje: getNamespaceResource(POKOJE, "en"),
    gdpr: getNamespaceResource(GDPR, "en"),
  },
  de: {
    global: getNamespaceResource(GLOBAL, "de"),
    home: getNamespaceResource(HOME, "de"),
    kontakt: getNamespaceResource(KONTAKT, "de"),
    restaurace: getNamespaceResource(RESTAURACE, "de"),
    galerie: getNamespaceResource(GALERIE, "de"),
    svatby: getNamespaceResource(SVATBY, "de"),
    ubytovani: getNamespaceResource(UBYTOVANI, "de"),
    balicky: getNamespaceResource(BALICKY, "de"),
    cenik: getNamespaceResource(CENIK, "de"),
    rezervace: getNamespaceResource(REZERVACE, "de"),
    pokoje: getNamespaceResource(POKOJE, "de"),
    gdpr: getNamespaceResource(GDPR, "de"),
  },
  pl: {
    global: getNamespaceResource(GLOBAL, "pl"),
    home: getNamespaceResource(HOME, "pl"),
    kontakt: getNamespaceResource(KONTAKT, "pl"),
    restaurace: getNamespaceResource(RESTAURACE, "pl"),
    galerie: getNamespaceResource(GALERIE, "pl"),
    svatby: getNamespaceResource(SVATBY, "pl"),
    ubytovani: getNamespaceResource(UBYTOVANI, "pl"),
    balicky: getNamespaceResource(BALICKY, "pl"),
    cenik: getNamespaceResource(CENIK, "pl"),
    rezervace: getNamespaceResource(REZERVACE, "pl"),
    pokoje: getNamespaceResource(POKOJE, "pl"),
    gdpr: getNamespaceResource(GDPR, "pl"),
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: getInitialLanguage(),
  fallbackLng: "cs",
  interpolation: { escapeValue: false },
  defaultNS: "global",
  ns: [
    "global",
    "home",
    "kontakt",
    "restaurace",
    "galerie",
    "svatby",
    "ubytovani",
    "balicky",
    "cenik",
    "rezervace",
    "pokoje",
    "gdpr",
  ],
});

i18n.on("languageChanged", (lng) => {
  const language = String(lng).split("-")[0];
  if (!SUPPORTED_LANGUAGES.includes(language)) return;

  if (typeof window !== "undefined") {
    window.localStorage.setItem("appLanguage", language);
  }
  if (typeof document !== "undefined") {
    document.documentElement.lang = language;
  }
});

export default i18n;

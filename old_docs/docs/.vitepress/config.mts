import { defineConfig } from "vitepress";

export default defineConfig({
  title: "Traitement Audio et Campus connecté",

  description: "Documentation for V2 Traitement Audio project",
  lang: "fr-FR",
  themeConfig: {
    // logo: "/logo.png",
    nav: [
      { text: "Accueil", link: "/" },
      {
        text: "Documentation",
        link: "/guide/",
      },
      {
        text: "Journal",
        items: [
          { text: "Vue d’ensemble", link: "/journal/" },
          { text: "5 Février 2026", link: "/journal/05-02-2026" },
          { text: "4 Février 2026", link: "/journal/04-02-2026" },
          { text: "3 Février 2026", link: "/journal/03-02-2026" },
          { text: "29 Janvier 2026", link: "/journal/29-01-2026" },
          { text: "27 Janvier 2026", link: "/journal/27-01-2026" },
          { text: "20 Janvier 2026", link: "/journal/20-01-2026" },
        ],
      },
      {
        text: "v2.0.0-master",
        items: [
          { text: "RoadMap", link: "https://roadmap-audio-projet.wagoo.app" },
          { text: "LICENSE", link: "/LICENSE" },
          {
            text: "API",
            link: "https://roadmap-audio-projet.wagoo.app/api/reference",
          },
        ],
      },
    ],

    editLink: {
      pattern:
        "https://forgens.univ-ubs.fr/gitlab/e2401623/traitement-audio-v2-2025-2026-snio-prj1401/edit/main/docs/:path",
      text: "Modifier cette page sur la forge de l'UBS",
    },

    footer: {
      message:
        'Le projet et cette documentation sont sous <a href="LICENSE.html">LICENCE</a>.',
      copyright: "Copyright © 2026 Université Bretagne Sud",
    },
    docFooter: {
      prev: "Page précédente",
      next: "Page suivante",
    },

    sidebar: {
      "/guide/": [
        {
          text: "Documentation",
          items: [
            { text: "Introduction", link: "/guide/" },
            {
              text: "Configuration",
              collapsed: true,
              items: [
                { text: "Introduction", link: "/guide/rpi/" },

                {
                  text: "Serveur",
                  collapsed: true,
                  items: [
                    {
                      text: "Raspberry pi",
                      link: "/guide/rpi/server/installation",
                    },
                    {
                      text: "Ordinateur (simple)",
                      link: "/guide/pc/server/",
                    },
                  ],
                },
                {
                  text: "Client",
                  collapsed: true,
                  items: [
                    {
                      text: "Raspberry pi",
                      link: "/guide/rpi/client/installation",
                    },
                  ],
                },
              ],
            },

            {
              text: "IqAudio Module",
              collapsed: true,
              items: [
                {
                  text: "Mise en place",
                  link: "/guide/module/carte-son/installation",
                },
                {
                  text: "Specification",
                  link: "/guide/module/carte-son/specification",
                },
              ],
            },
            {
              text: "GNU Radio",
              collapsed: true,
              items: [{ text: "Explication", link: "/guide/gnu-radio" }],
            },
            { text: "CLI", link: "/guide/cli" },
          ],
        },
      ],
      "/journal/": [
        {
          text: "Journal",
          items: [
            { text: "Vue d’ensemble", link: "/journal/" },
            {
              text: "Semaine du 2 Février",
              items: [
                { text: "5 Février 2026", link: "/journal/05-02-2026" },
                { text: "4 Février 2026", link: "/journal/04-02-2026" },
                { text: "3 Février 2026", link: "/journal/03-02-2026" },
              ],
            },
            {
              text: "Semaine du 26 Janvier",
              items: [
                { text: "29 Janvier 2026", link: "/journal/29-01-2026" },
                { text: "27 Janvier 2026", link: "/journal/27-01-2026" },
              ],
            },
            {
              text: "Semaine du 19 Janvier",
              items: [{ text: "20 Janvier 2026", link: "/journal/20-01-2026" }],
            },
          ],
        },
        { text: "Changelog (soon)", link: "/journal/CHANGELOG" },
      ],
      "/api/": [{ text: "API", link: "/api/" }],
    },
    socialLinks: [
      {
        icon: "github",
        link: "https://forgens.univ-ubs.fr/gitlab/e2401623/traitement-audio-v2-2025-2026-snio-prj1401",
      },
    ],
  },
});

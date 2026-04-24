import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "PRJ1401",
  description: "Traitement audio et diffusion sur un reseau IP",
  titleTemplate: ":title - V2 PRJ1401",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Accueil", link: "/" },
      { text: "Documentation", link: "/docs" },
    ],

    sidebar: [
      {
        text: "Documentation",
        items: [
          { text: "Introduction", link: "/docs/index" },
          {
            text: "Etude",
            collapsed: true,
            items: [
              {
                text: "GNU RADIO",
                collapsed: true,
                items: [
                  {
                    text: "introduction",
                    link: "/docs/etude/gnuradio/introduction",
                  },
                  { text: "tcp", link: "/docs/etude/gnuradio/tcp" },
                  { text: "udp", link: "/docs/etude/gnuradio/udp" },
                  { text: "zmq", link: "/docs/etude/gnuradio/zmq" },
                ],
              },
              {
                text: "Protocoles",
                collapsed: true,
                items: [
                  {
                    text: "introduction",
                    link: "/docs/etude/protocoles/intro",
                  },
                  { text: "rtp", link: "/docs/etude/protocoles/rtp" },
                  { text: "tcp", link: "/docs/etude/protocoles/tcp" },
                  { text: "udp", link: "/docs/etude/protocoles/udp" },
                  { text: "srtp", link: "/docs/etude/protocoles/srtp" },
                ],
              },
            ],
          },
          {
            text: "Raspberry PI",
            collapsed: true,
            items: [
              { text: "Introduction", link: "/docs/raspberrypi/" },
              { text: "installation", link: "/docs/raspberrypi/installation" },
            ],
          },
          {
            text: "Application",
            collapsed: true,
            items: [
              { text: "Introduction", link: "/docs/application/" },
              {
                text: "Fonctionnement",
                link: "/docs/application/fonctionnement",
              },
              {
                text: "Hôte",
                collapsed: true,
                items: [
                  {
                    text: "Installation",
                    link: "/docs/application/host/installation",
                  },
                  {
                    text: "Fonctionnalité",
                    link: "/docs/application/host/fonctionnalite",
                  },
                ],
              },
              {
                text: "Client",
                collapsed: true,
                items: [
                  {
                    text: "Installation",
                    link: "/docs/application/client/installation",
                  },
                  {
                    text: "Fonctionnalité",
                    link: "/docs/application/client/fonctionnalite",
                  },
                ],
              },
            ],
          },
           {
                    text: "Licence",
                    link: "/docs/license",
                  },
          {
                    text: "Securité",
                    link: "/docs/security",
                  },
        ],
      },
    ],

    socialLinks: [
      { icon: "github", link: "https://github.com/vuejs/vitepress" },
    ],
  },
});

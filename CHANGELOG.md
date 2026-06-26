# Changelog

Alle nennenswerten Änderungen werden hier dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).
Versionierung folgt [Semantic Versioning](https://semver.org/lang/de/).

## 1.0.0 (2026-06-26)


### Features

* **api:** add offer list/detail/status-update endpoints ([edad44e](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/edad44ebba5796e37ee24d3b0489c7e5013ad66c))
* configure project identity for stratpool-angebote-app ([1570a55](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/1570a553e9a03e04c4fe141cc5d795fafdb2c60b))
* **db:** add ORM models and baseline migration for offers schema ([5b37b2f](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/5b37b2fb1a8b275c410484d3827addfeee0e0bc0))
* **frontend:** add /angebote/neu generation form with section preview ([fc6e46d](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/fc6e46dbd21e418b75460acd39eae753c70a9a1d))
* **frontend:** add offer list and detail pages with status updates ([bde3559](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/bde3559d4ba726b072fa951f7dc2d03c61438bca))
* **generate:** async offer generation via Arq worker ([157c291](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/157c291de9b847b7541ead326086ff0c7d18d660))
* **generate:** bump max_tokens 16k → 32k for richer v2 output ([aac4800](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/aac4800f1ee12fe4b09a4034faebb18623f15e19))
* **hedy:** integrate Hedy session picker into new-offer form ([4fadc44](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/4fadc44dde134d84b00491efc18b38326c5e7b6f))
* **nav:** add back-to-list links from new-offer flow ([1aea74e](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/1aea74e0b613c86faa1c53a793dc44a3787c3404))
* **offers:** add generation pipeline (embed → retrieve → Claude → persist) ([405638e](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/405638e840e99e0ecc2a28f132081b34622b0798))
* **offers:** edit content before render, save as new version ([48e9b1e](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/48e9b1e66d8d065135ed428a755fdb2092de13c7))
* **prompts:** read-only prompt viewer for both pipelines ([d15aa39](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/d15aa3986ef0c8e37419b781a2f990c734a5649f))
* **render:** async render via worker + polling ([6e4f825](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/6e4f82502a1f59d8ba5c0ba05757ac2d754d7cf1))
* **render:** force-flag for skill-iteration + Saarpor-pattern SKILL.md ([0b974f0](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/0b974f0af2d7d403f6c35dfbc3a43c10fab703ef))
* **render:** skill-driven PPT pipeline + co-consultant directory ([9c84af7](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/9c84af7565e0b11e43ef82918494331d48d3735d))
* **render:** word output via era-word skill + format param ([f7a24f2](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/f7a24f200d2259ef8fc53631cceb02f2a98dcf3b))
* **seed:** add seeding pipeline for historical offers ([b8e8953](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/b8e895308648551855a99a0f56c562ebb9cb7aaa))
* **skill:** add ERA logo helper + harden Investition slide ([0ba6909](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/0ba6909bab3a5a0a5ed21116bbfca045332c2832))
* storytelling schema v2 + knowledge base + render-skill recipes ([fad45d9](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/fad45d9f2f85461acb96ab2482e4fd7779999c7c))
* **versions:** add version-history UI and read-only past-version view ([2be47e7](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/2be47e7af1c5b428c444a1e1dce3c7ac45c16b84))


### Bug Fixes

* **ci:** declare pnpm version via packageManager field ([58048d6](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/58048d61787a3bff9076b97a300adc13bc088f9f))
* **ci:** pin pnpm version directly in workflow ([f620fb3](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/f620fb38e4bfad1f779fc4604211f02dcfe42f8b))
* **compose:** join backend to supabase docker network ([b0f594b](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/b0f594ba5d928f8a9d73baa0e72534c1b0f8a407))
* **compose:** single named traefik service, route both http+https to it ([b4e5a9f](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/b4e5a9fa9423500f52e1676a4ca298805b217cdf))
* **compose:** use 127.0.0.1 in healthchecks instead of localhost ([0893a17](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/0893a17aafd31d821da0c18a18365cdd1a45b574))
* **db:** align ORM with Supabase auth schema and pull in greenlet ([35c37bf](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/35c37bfe277ed5da2d184b058e0b05ea0e7881e0))
* **download:** use anchor click instead of window.open after long await ([9944d94](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/9944d94b64736ca9ce2d18f701ee318c730e4d39))
* **frontend:** relax price step to accept any value ([3040cbc](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/3040cbc2df928b9bcdd371a23892ba8b8c780d2c))
* **frontend:** render buttons on preview + relax price step ([770fa51](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/770fa51c6e1bd689a8a25a236b6b2aaee09bb62a))
* **generate:** tolerate bestandteile arriving as a JSON string ([b6511a5](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/b6511a596cb7334520d6bec4f1913ca65f20cc28))
* **generate:** tolerate Claude wrapping payload under a single-key wrapper ([509fd12](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/509fd125715f2062aece5fbc4b9637e318d40dac))
* **generate:** use streaming API for the long-output request ([e107a46](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/e107a46c0c8dc9c8e3dea1e1b14c2a0bbda757c7))
* **offers:** exclude legacy pool entries from list and detail ([869fccd](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/869fccddc143b996d726742aeb5a644083712cbc))
* **prompts:** pass knowledge=[] to _build_user_message in viewer ([8dcb5e7](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/8dcb5e76ad0a3833788448095f738746a5c75c36))
* **render:** bump max_tokens to 32k + use streaming API ([f0977ff](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/f0977ff000f9bc2a1ffdc5dd467ac1c54119d2d6))
* **render:** write pptx to $OUTPUT_DIR so Files API picks it up ([fb5e236](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/fb5e236d52dc9089ef145ad4a6c7c98f48eb1620))
* **routing:** pin traefik to the Coolify-managed app network ([b68272b](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/b68272bae18a1cd97a1da446b29f4cf0c6e4edf6))
* **schema:** coerce Opus over-length lists and dict bullets instead of failing generation ([380bdd5](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/380bdd5b613c6f49c6a81ac163da2778787e6ab5))
* **schema:** handle literal \\n in JSON-string list payloads ([28cc678](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/28cc678d1d3f1af0607ec056ef55c5e5f6160ea9))
* **schema:** recover Claude tool-use payloads with stray quotes ([9ccbd42](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/9ccbd42f2c70154c4527d87b2b84fc4aa455afa3))
* **seed:** commit per offer and throttle for Voyage free tier ([14281e6](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/14281e6d460450970b375f105220074eec6bb935))
* **seed:** strip NUL + control chars from PDF text + use asyncpg URL ([420e356](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/420e35647f66d62a7cde479254c46c13d2322c67))
* **worker:** wrap worker exceptions in pickle-safe RuntimeError ([e8cd931](https://github.com/thomasbrunner-spec/stratpool-angebote-app/commit/e8cd931cd23e38e4f2f086c3328e39d39e511d98))

## [0.1.0] - 2026-05-07

### Added
- FastAPI backend mit Anthropic + Voyage AI Integration
- Next.js 15 Frontend mit Supabase Auth
- Hello-World Endpoint mit echtem Anthropic API Call
- Health Check Endpoints (DB, Anthropic, Voyage, Full)
- Docker Compose Setup für Coolify
- GitHub Actions: CI + Release Please
- Stratpool Design System integriert

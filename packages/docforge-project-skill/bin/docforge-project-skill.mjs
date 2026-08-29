#!/usr/bin/env node

import { main } from "../docforge-project/scripts/docforge-project.mjs";

await main(process.argv.slice(2));

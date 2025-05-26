import fs from 'fs';
import vm from 'vm';
import path from 'path';

const file = path.resolve(process.argv[2]);
const code = fs.readFileSync(file, 'utf8');
const context = vm.createContext({ console, process: { env: { ...process.env } } });
const mod = new vm.SourceTextModule(code, { context, identifier: file });

const linker = async (specifier) => {
  if (specifier === 'next-auth') {
    return new vm.SourceTextModule('export default (o) => o;', { context });
  }
  if (specifier === 'next-auth/providers/credentials') {
    return new vm.SourceTextModule('export default (o) => ({ id: "credentials", opts: o });', { context });
  }
  if (specifier === 'next-auth/providers/google') {
    return new vm.SourceTextModule('export default (o) => ({ id: "google", opts: o });', { context });
  }
  if (specifier === 'next-auth/providers/okta') {
    return new vm.SourceTextModule('export default (o) => ({ id: "okta", opts: o });', { context });
  }
  if (specifier === 'next-auth/providers/saml') {
    return new vm.SourceTextModule('export default (o) => ({ id: "saml", opts: o });', { context });
  }
  throw new Error('Unknown module ' + specifier);
};

await mod.link(linker);
await mod.evaluate();
console.log(JSON.stringify(mod.namespace.default));


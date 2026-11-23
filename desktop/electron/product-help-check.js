'use strict';
/** Check actual rendered text against the canonical contract, not merely an ID. */
const contract = require('../src/core/product-contract');
function verifyProductHelp(snapshot) {
  if (!snapshot || JSON.stringify(snapshot.contract) !== JSON.stringify(contract)) return false;
  if (typeof snapshot.intro !== 'string' || typeof snapshot.scenarios !== 'string') return false;
  const fields = ['name', 'platform', 'entry', 'state', 'delivery', 'network', 'hardware', 'rights'];
  return fields.every(key => snapshot.intro.includes(contract[key])) && contract.scenarios.every(s =>
    [s.name, s.result, s.blocker, s.accepted ? 'Принят: ' : 'Не принят: '].every(text => snapshot.scenarios.includes(text)));
}
module.exports = { verifyProductHelp };

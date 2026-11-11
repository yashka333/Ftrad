// Dumps the frog rules from the shared package as JSON for the browser demos.
import { RARITIES, SKILLS, SKILL_WEIGHT, ECONOMY, MARKET, INVITE } from '../../../shared/src/index.js';
const names = ['Bagholder Bob', 'Chartie', 'Rugpull Ron', 'Ape Andy', 'Wick Willy', 'Paper Paul',
  'Diamond Dee', 'Leverage Larry', 'Fomo Fred', 'Shorty', 'Candle Carl', 'Pump Pete',
  'Gwei Greg', 'Stop-Loss Sam', 'Moon Mo', 'Dip Dan', 'Exit Liquidity Eli', 'Rekt Rick',
  'Hodl Hank', 'Sniper Sid', 'Floor Flo', 'Gas Gus', 'Liquidated Liz', 'Pivot Pat',
  'Scalper Sal', 'Whale Wally', 'Jeet Jim', 'Copium Cody', 'Alpha Al', 'Bear Bart'];
console.log(JSON.stringify({ rarities: RARITIES, skills: SKILLS, skillWeight: SKILL_WEIGHT, packPrice: ECONOMY.packPrice, withdraw: ECONOMY.withdraw, faucet: ECONOMY.devFaucetAmount, market: MARKET, invite: INVITE, names }));

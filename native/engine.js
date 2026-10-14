import {DATA} from './content.js';
import {seed,object,integer,equal,encodeState,decodeState} from './core.js';
export const groups=DATA.groups;
const keys=['v','s','o','d','g','a','n','e','r','t'];
const check=(ok)=>{if(!ok)throw Error('Invalid saved model');};
export function newState(){return {v:3,s:0,o:seed(),d:Object.fromEntries(groups.map(g=>[g.id,{}])),g:{},a:{},n:{},e:{},r:{},t:{}};}
export function correct(g,answers){return g.fields.every(f=>answers[f.id]===f.answer);}
export function validate(s){check(object(s)&&Object.keys(s).length===keys.length&&keys.every(k=>Object.hasOwn(s,k))&&[2,3].includes(s.v)&&integer(s.s,0,6)&&typeof s.o==='bigint'&&s.o>=0n&&s.o<2n**63n);check(object(s.d)&&Object.keys(s.d).length===5&&object(s.t));for(const g of groups){const valid=map=>object(map)&&Object.entries(map).every(([k,v])=>g.fields.some(f=>f.id===k&&f.options.includes(v)));check(valid(s[g.key])&&valid(s.d[g.id]));if(g.stage>s.s)check(Object.keys(s[g.key]).length===0&&Object.keys(s.d[g.id]).length===0);if(g.stage<s.s)check(correct(g,s[g.key]));if(s.v===2&&Object.keys(s[g.key]).length)check(equal(s[g.key],s.d[g.id]));if(g.stage<s.s)check(equal(s[g.key],s.d[g.id]));}check(Object.entries(s.t).every(([k,v])=>groups.some(g=>g.id===k)&&integer(v,1,s.v===2?99:1000000)));return s;}
export async function read(token){try{return validate(await decodeState(token));}catch{return null;}}
export async function write(s){return encodeState(validate(s));}
export class Lesson{
 constructor(state=newState(),view){this.state=validate(state);const n=Number(view);this.view=view!==null&&view!==undefined&&/^\d+$/.test(String(view))&&integer(n,0,state.s)?n:state.s;}
 get reached(){return this.state.s;}get shownStage(){return this.view;}get total(){return 7;}get reviewing(){return this.view<this.reached;}get group(){return groups.find(g=>g.stage===this.state.s);}get locked(){return this.group&&correct(this.group,this.state[this.group.key]);}
 move(d){if(![-1,1].includes(d)||!integer(this.view+d,0,this.reached))return false;this.view+=d;return true;}
 draft(id,value){if(this.reviewing||!this.group||this.locked||!this.group.fields.some(f=>f.id===id&&f.options.includes(value)))return false;this.state.v=3;this.state.d[this.group.id][id]=value;return true;}
 submit(){if(this.reviewing||!this.group||this.locked)return false;const g=this.group,d=this.state.d[g.id];if(!g.fields.every(f=>f.options.includes(d[f.id])))return false;this.state[g.key]={...d};this.state.t[g.id]=(this.state.t[g.id]??0)+1;this.state.v=3;return true;}
 advance(){if(this.reviewing||this.state.s===6||this.state.s!==0&&!this.locked)return false;this.state.s++;this.view=this.state.s;return true;}
}

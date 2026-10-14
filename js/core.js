/** Shared native helpers. Derived from the accepted Receivables implementation. */
export const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v)&&Object.getPrototypeOf(v)===Object.prototype;
const assert=(ok,message)=>{if(!ok)throw Error(message);};
export const integer=(v,min,max)=>Number.isSafeInteger(v)&&v>=min&&v<=max;
export const equal=(a,b)=>canonicalJSON(a)===canonicalJSON(b);
export function seed(){const a=crypto.getRandomValues(new Uint32Array(2));return (BigInt(a[0])<<31n)|BigInt(a[1]>>>1);}
export function parseJSON(text){text=text.replace(/("(?:z|o)"\s*:\s*)(\d+)(?=\s*[,}])/g,'$1"$2"');const s=JSON.parse(text);for(const k of ['z','o'])if(k in s){if(typeof s[k]!=='string'||!/^\d{1,19}$/.test(s[k]))throw Error('Invalid seed');s[k]=BigInt(s[k]);}return s;}
export function canonicalJSON(value) {
  if(typeof value==='bigint') return value.toString();
  if(Array.isArray(value)) return `[${value.map(canonicalJSON).join(',')}]`;
  if(object(value)) return `{${Object.keys(value).sort().map(key=>`${JSON.stringify(key)}:${canonicalJSON(value[key])}`).join(',')}}`;
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g,c=>`\\u${c.charCodeAt(0).toString(16).padStart(4,'0')}`);
}
function base64url(bytes) {
  let text='';for(const byte of bytes)text+=String.fromCharCode(byte);
  return btoa(text).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/g,'');
}
function from64(text) {
  assert(typeof text==='string'&&text.length>0&&text.length<=64000&&/^[\w-]+$/.test(text),'Invalid token');
  return Uint8Array.from(atob(text.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-text.length%4)%4)),c=>c.charCodeAt(0));
}
async function transform(bytes,stream,max) {
  const reader=new Blob([bytes]).stream().pipeThrough(stream).getReader();
  const chunks=[];let length=0;
  while(true) {
    const {done,value}=await reader.read();if(done)break;
    length+=value.length;
    if(length>max){await reader.cancel();throw new Error('Saved state too large');}
    chunks.push(value);
  }
  const output=new Uint8Array(length);let offset=0;
  for(const chunk of chunks){output.set(chunk,offset);offset+=chunk.length;}
  return output;
}
export async function encodeState(state) {
  const normalized=state;
  const bytes=new TextEncoder().encode(canonicalJSON(normalized));
  assert(bytes.length<=128000,'Saved state too large');
  return base64url(await transform(bytes,new CompressionStream('deflate'),64000));
}
export async function decodeState(token) {
  try {
    const bytes=await transform(from64(token),new DecompressionStream('deflate'),128000);
    return parseJSON(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  } catch {return null;}
}class PythonRandom {
  constructor(seed) {
    const words=[];do{words.push(Number(seed&0xffffffffn));seed>>=32n;}while(seed);
    this.mt=new Uint32Array(624);this.mt[0]=19650218;
    for(let i=1;i<624;i++)this.mt[i]=(Math.imul(1812433253,this.mt[i-1]^(this.mt[i-1]>>>30))+i)>>>0;
    let i=1,j=0;
    for(let k=Math.max(624,words.length);k>0;k--) {
      this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1664525))+words[j]+j)>>>0;
      if(++i>=624){this.mt[0]=this.mt[623];i=1;}if(++j>=words.length)j=0;
    }
    for(let k=623;k>0;k--) {
      this.mt[i]=((this.mt[i]^Math.imul(this.mt[i-1]^(this.mt[i-1]>>>30),1566083941))-i)>>>0;
      if(++i>=624){this.mt[0]=this.mt[623];i=1;}
    }
    this.mt[0]=0x80000000;this.index=624;
  }
  next() {
    if(this.index>=624) {
      for(let i=0;i<624;i++) {
        const value=(this.mt[i]&0x80000000)|(this.mt[(i+1)%624]&0x7fffffff);
        this.mt[i]=(this.mt[(i+397)%624]^(value>>>1)^((value&1)?0x9908b0df:0))>>>0;
      }
      this.index=0;
    }
    let value=this.mt[this.index++];value^=value>>>11;value^=(value<<7)&0x9d2c5680;value^=(value<<15)&0xefc60000;value^=value>>>18;
    return value>>>0;
  }
  below(n) {const bits=n.toString(2).length;let value;do{value=this.next()>>>(32-bits);}while(value>=n);return value;}
}
export async function shuffled(input,seed,salt) {
  const bytes=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(`${seed}:${salt}`)));
  let number=0n;for(const byte of bytes.slice(0,8))number=(number<<8n)|BigInt(byte);
  const random=new PythonRandom(number),result=[...input];
  for(let i=result.length-1;i>0;i--){const j=random.below(i+1);[result[i],result[j]]=[result[j],result[i]];}
  if(result.length>1&&result.every((value,index)=>value===input[index]))return [...result.slice(1),result[0]];
  return result;
}

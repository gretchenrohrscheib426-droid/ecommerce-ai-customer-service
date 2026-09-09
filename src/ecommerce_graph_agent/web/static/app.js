'use strict';
const form=document.querySelector('#chat-form'),input=document.querySelector('#question'),send=document.querySelector('#send'),cancel=document.querySelector('#cancel'),status=document.querySelector('#status'),messages=document.querySelector('#messages');
let busy=false,composing=false,controller=null;
function append(role,text){const article=document.createElement('article');article.className=role;const title=document.createElement('b');title.textContent=role==='user'?'您':'图谱助手';const p=document.createElement('p');p.textContent=text;article.append(title,p);messages.append(article);messages.scrollTop=messages.scrollHeight;return article;}
async function submit(message,clarification={}){
 if(busy||!message.trim())return;
 if(message.length>500){status.textContent='问题不能超过 500 字。';return;}
 busy=true;send.disabled=true;cancel.hidden=false;controller=new AbortController();status.textContent='正在查找实体与证据…';
 append('user',clarification.choice?'已确认实体：'+clarification.choice:message);
 const timer=setTimeout(()=>controller?.abort('timeout'),45000);
 try{
  const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,...clarification}),signal:controller.signal});
  if(!response.ok)throw new Error('服务返回 HTTP '+response.status+'，请检查服务后重试。');
  if(!response.headers.get('content-type')?.includes('application/json'))throw new Error('响应格式异常。');
  const result=await response.json();if(typeof result.message!=='string')throw new Error('响应缺少回答。');
  const article=append('bot',result.message);
  if(result.evidence?.length){const details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='查看实际证据 · '+result.evidence.length+' 条';pre.textContent=JSON.stringify(result.evidence,null,2);details.append(summary,pre);article.append(details);}
  for(const candidate of result.candidates||[]){const button=document.createElement('button');button.type='button';button.className='choice';button.textContent=candidate.canonical_name+' · '+candidate.label+' · '+candidate.canonical_id;button.onclick=()=>{if(!busy){article.querySelectorAll('.choice').forEach(b=>b.disabled=true);submit(message,{choice:candidate.canonical_id,clarification_token:result.clarification_token});}};article.append(button);}
  status.textContent='状态：'+result.status+' · '+(result.generation||'')+' · 追踪 '+(result.trace_id||'');
 }catch(error){const message=controller.signal.aborted?'请求已取消或超时，可重新发送。':error.message;append('bot',message);status.textContent=message;}
 finally{clearTimeout(timer);busy=false;controller=null;send.disabled=false;cancel.hidden=true;}
}
form.addEventListener('submit',event=>{event.preventDefault();if(!composing)submit(input.value.trim());});
input.addEventListener('compositionstart',()=>composing=true);input.addEventListener('compositionend',()=>composing=false);
input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing&&!composing&&event.keyCode!==229){event.preventDefault();submit(input.value.trim());}});
cancel.addEventListener('click',()=>controller?.abort());
document.querySelectorAll('[data-question]').forEach(button=>button.addEventListener('click',()=>{if(!busy){input.value=button.dataset.question;submit(input.value);}}));
fetch('/api/status').then(async response=>{if(!response.ok)throw new Error();return response.json();}).then(value=>{
 const ready=value.neo4j==='ok'&&value.embedding==='loaded';
 document.querySelector('#mode').textContent=ready?'离线演示 · 本地规则与事实模板':'服务未就绪';
 document.querySelector('#service-dot').classList.toggle('ready',ready);
 document.querySelector('#dependencies').textContent='MySQL: '+value.mysql+' · Neo4j: '+value.neo4j+' · LLM: '+value.llm+' · NER: '+value.ner_model+' · '+value.generation;
 if(value.llm==='configured_not_probed') document.querySelector('#mode').textContent='在线模式已配置 · 尚未探测';
}).catch(()=>{document.querySelector('#mode').textContent='服务未就绪，请检查本地运行日志';document.querySelector('#dependencies').textContent='依赖状态不可用';});

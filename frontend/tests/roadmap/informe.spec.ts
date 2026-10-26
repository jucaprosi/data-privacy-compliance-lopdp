import { expect, test } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

test("Descargar informe (PDF) solicita el PDF al servidor", async ({ page }) => {
  const descargas: string[]=[];
  await page.addInitScript(() => localStorage.setItem("lopdp-roadmap-store-v1",JSON.stringify({state:{currentRoadmapId:"rm-report",statusFilter:"todas",priorityFilter:"todas",areaFilter:"todas"},version:0})));
  await page.route("**/api/v1/**",async route=>{
    const p=new URL(route.request().url()).pathname.replace(/^\/api\/v1/,"");
    if(p==="/organizacion/me/roles") return route.fulfill({json:[{role:"implementador",area_id:null}]});
    if(["/organizacion/usuarios","/organizacion/areas","/organizacion/roles"].includes(p)) return route.fulfill({json:[]});
    if(p==="/roadmaps/rm-report/informe.pdf"){ descargas.push(p); return route.fulfill({contentType:"application/pdf",body:Buffer.from("%PDF-1.4 simulado")}); }
    if(p==="/roadmaps/rm-report") return route.fulfill({json:{roadmap:{id:"rm-report",summary:"Ruta"},waves:[{id:"w1",name:"Ola 1",sort_order:1,tasks:[]}]}});
    if(p==="/roadmaps/rm-report/kpis") return route.fulfill({json:{total_tareas:0,completadas:0,criticas:0,altas:0,progreso_porcentaje:0}});
    return route.fulfill({status:404,json:{detail:"No simulado"}});
  });
  await abrirAppLimpia(page); await configurarProyecto(page,"Entidad RM-20"); await irASala(page,/^Hoja de Ruta/);
  await page.getByRole("button",{name:"Olas & Tareas",exact:true}).click();
  await page.getByRole("button",{name:"Descargar informe (PDF)"}).click();
  await expect.poll(()=>descargas).toEqual(["/roadmaps/rm-report/informe.pdf"]);
});

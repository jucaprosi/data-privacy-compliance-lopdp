import React, { useEffect, useState } from 'react';
import { BookOpen, FileCheck } from 'lucide-react';
import { useAuditStore } from "@/store/useAuditStore";

export default function NiifDoctrinaView() {
  const { doctrinaData, setDoctrinaData } = useAuditStore();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!doctrinaData) {
      setIsLoading(true);
      fetch("/api/v1/niif18/doctrina")
        .then(res => res.json())
        .then(data => setDoctrinaData(data))
        .catch(err => console.error(err))
        .finally(() => setIsLoading(false));
    }
  }, [doctrinaData, setDoctrinaData]);

  return (
    <div className="flex flex-col h-full bg-[#0a0a0c] text-zinc-100 p-6 space-y-4">
      <div className="flex items-center space-x-3 mb-4">
        <BookOpen className="w-6 h-6 text-[#9a3bf1]" />
        <h2 className="text-xl font-bold">Visor Doctrinal NIIF 18</h2>
      </div>
      
      <div className="bg-[#141417] border border-[#26262b] rounded-lg p-6 flex-1 overflow-y-auto">
        <div className="flex items-center space-x-2 mb-4 text-zinc-300">
          <FileCheck className="w-5 h-5 text-emerald-500" />
          <h3 className="text-lg font-semibold">Párrafos Clave de la Normativa</h3>
        </div>
        
        {isLoading ? (
          <div className="flex justify-center items-center py-20">
            <span className="animate-pulse text-zinc-500">Cargando biblioteca doctrinal...</span>
          </div>
        ) : !doctrinaData || Object.keys(doctrinaData).length === 0 ? (
          <div className="p-4 bg-[#1e1e24] border border-[#26262b] rounded-md">
            <p className="font-mono text-xs text-zinc-500">
              * El contenido normativo oficial no está disponible en este momento.
            </p>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(doctrinaData).map(([filename, content]) => (
              <div key={filename} className="border border-zinc-800 rounded-lg p-5 bg-[#0a0a0c]">
                <h4 className="text-blue-400 font-semibold border-b border-zinc-800 pb-2 mb-3">{filename}</h4>
                <div className="text-sm text-zinc-300 whitespace-pre-wrap font-mono leading-relaxed">
                  {content as string}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

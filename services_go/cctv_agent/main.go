// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤motor-go-hibrido ¤videovigilancia-cctv ¤boveda-cloud
package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Println("Evydentia CCTV Edge Agent v1.0.0 (Go Satellite)")
	if len(os.Args) < 2 {
		fmt.Println("Usage: cctv_agent <config.json>")
		os.Exit(0)
	}
}

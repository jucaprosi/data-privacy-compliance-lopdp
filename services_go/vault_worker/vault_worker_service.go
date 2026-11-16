// ¤motor-go-hibrido ¤boveda-cloud ¤conservacion
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"time"
)

type VaultIngestEvent struct {
	TenantID  string `json:"tenant_id"`
	ObjectKey string `json:"object_key"`
	SizeBytes int64  `json:"size_bytes"`
	SHA256Hex string `json:"sha256_hex"`
	Bucket    string `json:"bucket"`
}

type VaultPurgeBatchResult struct {
	PoliticaID             string `json:"politica_id"`
	ObjetosEliminadosCount int    `json:"objetos_eliminados_count"`
	ActaLoteSHA256         string `json:"acta_lote_sha256"`
	TimestampUTC           string `json:"timestamp_utc"`
}

func StreamHashSHA256(r io.Reader) (string, int64, error) {
	hasher := sha256.New()
	buf := make([]byte, 64*1024)
	n, err := io.CopyBuffer(hasher, r, buf)
	if err != nil {
		return "", 0, fmt.Errorf("error stream hashing: %w", err)
	}
	return hex.EncodeToString(hasher.Sum(nil)), n, nil
}

func SignPayload(secret []byte, data []byte) string {
	mac := hmac.New(sha256.New, secret)
	mac.Write(data)
	return hex.EncodeToString(mac.Sum(nil))
}

func VerifySignature(secret []byte, data []byte, signature string) bool {
	expected := SignPayload(secret, data)
	return hmac.Equal([]byte(expected), []byte(signature))
}

func ExecutePurgeBatch(politicaID string, objectKeys []string) VaultPurgeBatchResult {
	hasher := sha256.New()
	for _, key := range objectKeys {
		hasher.Write([]byte(key + "\n"))
	}
	actaHash := hex.EncodeToString(hasher.Sum(nil))
	return VaultPurgeBatchResult{
		PoliticaID:             politicaID,
		ObjetosEliminadosCount: len(objectKeys),
		ActaLoteSHA256:         actaHash,
		TimestampUTC:           time.Now().UTC().Format(time.RFC3339),
	}
}

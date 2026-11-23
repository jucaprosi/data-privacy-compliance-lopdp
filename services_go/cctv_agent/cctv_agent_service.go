// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤motor-go-hibrido ¤videovigilancia-cctv ¤boveda-cloud
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
)

type Config struct {
	TenantID                string `json:"tenant_id"`
	CamaraID                string `json:"camara_id"`
	CodecRequired           string `json:"codec_required"`
	StripAudio              bool   `json:"strip_audio"`
	MaxSegmentSeconds       int    `json:"max_segment_seconds"`
	UploadSignedURLEndpoint string `json:"upload_signed_url_endpoint"`
}

type ClipTelemetry struct {
	ClipID     string `json:"clip_id"`
	TenantID   string `json:"tenant_id"`
	CamaraID   string `json:"camara_id"`
	SHA256Hash string `json:"sha256_hash"`
	StripAudio bool   `json:"strip_audio"`
	HasAudio   bool   `json:"has_audio"`
	SizeBytes  int64  `json:"size_bytes"`
}

func ProcessSegment(cfg Config, input io.Reader, hasAudio bool) (*ClipTelemetry, error) {
	if !cfg.StripAudio {
		return nil, errors.New("strip_audio must be true to comply with LOPDP")
	}
	if hasAudio {
		return nil, errors.New("input stream contains audio track; stripping required before upload")
	}

	hasher := sha256.New()
	written, err := io.Copy(hasher, input)
	if err != nil {
		return nil, fmt.Errorf("failed calculating stream SHA-256: %w", err)
	}

	hashStr := hex.EncodeToString(hasher.Sum(nil))
	return &ClipTelemetry{
		ClipID:     fmt.Sprintf("clip-%s-%s", cfg.CamaraID, hashStr[:12]),
		TenantID:   cfg.TenantID,
		CamaraID:   cfg.CamaraID,
		SHA256Hash: hashStr,
		StripAudio: true,
		HasAudio:   false,
		SizeBytes:  written,
	}, nil
}

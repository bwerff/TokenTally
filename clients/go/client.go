package tokentally

import (
    "encoding/json"
    "fmt"
    "net/http"
)

type usageResponse struct {
    Result struct {
        Data []map[string]interface{} `json:"data"`
    } `json:"result"`
}

func GetUsage(baseURL string) ([]map[string]interface{}, error) {
    resp, err := http.Get(fmt.Sprintf("%s/api/trpc/usage", baseURL))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("status %d", resp.StatusCode)
    }
    var r usageResponse
    if err := json.NewDecoder(resp.Body).Decode(&r); err != nil {
        return nil, err
    }
    return r.Result.Data, nil
}

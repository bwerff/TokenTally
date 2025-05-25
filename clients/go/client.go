package tokentally

import (
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

type usageResponse struct {
    Result struct {
        Data []map[string]interface{} `json:"data"`
    } `json:"result"`
}

func GetUsage(baseURL string) ([]map[string]interface{}, error) {
    delay := 100 * time.Millisecond
    for i := 0; i < 3; i++ {
        resp, err := http.Get(fmt.Sprintf("%s/api/trpc/usage", baseURL))
        if err == nil && resp.StatusCode == http.StatusOK {
            defer resp.Body.Close()
            var r usageResponse
            if err := json.NewDecoder(resp.Body).Decode(&r); err != nil {
                return nil, err
            }
            return r.Result.Data, nil
        }
        if resp != nil {
            resp.Body.Close()
        }
        if i == 2 {
            if err != nil {
                return nil, err
            }
            return nil, fmt.Errorf("status %d", resp.StatusCode)
        }
        time.Sleep(delay)
        delay *= 2
    }
    return nil, fmt.Errorf("unreachable")
}
